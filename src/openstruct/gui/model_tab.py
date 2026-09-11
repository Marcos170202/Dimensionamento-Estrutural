"""Aba "Modelo e Analise": monta o modelo, roda a analise, mostra os resultados.

Camada fina sobre ``openstruct.domain``/``openstruct.results`` — todas
as classes/funcoes usadas aqui (``Node``, ``Material``, ``Section``,
``Element3D``, ``Support``, ``NodalLoad``, ``LoadCase``,
``AnalysisModel``, ``self_weight_loads``, ``run_analysis``) ja existem
e sao testadas/validadas em ``tests/``; este modulo so faz a ponte
entre as tabelas da GUI e essas chamadas.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from openstruct import run_analysis
from openstruct.domain import (
    AnalysisModel,
    Element3D,
    ElementLoad,
    LoadCase,
    Material,
    NodalLoad,
    Node,
    Section,
    Support,
    self_weight_loads,
)
from openstruct.results import AnalysisResult

from ._parsing import parse_decimal
from .widgets import EditableTable

_NODE_COLUMNS = ["ID", "X (mm)", "Y (mm)", "Z (mm)"]
_MATERIAL_COLUMNS = [
    "Nome", "E (MPa)", "G (MPa)", "density (kg/mm³)", "fy (MPa)", "fu (MPa)", "poisson",
]
_SECTION_COLUMNS = [
    "Nome", "A (mm²)", "Iy (mm⁴)", "Iz (mm⁴)", "J (mm⁴)",
    "Wply (mm³)", "Wplz (mm³)", "Wely (mm³)", "Welz (mm³)", "Cw (mm⁶, opcional)",
]
_ELEMENT_COLUMNS = ["ID", "Nó I", "Nó J", "Material (nome)", "Seção (nome)"]
_SUPPORT_COLUMNS = ["Nó", "UX", "UY", "UZ", "RX", "RY", "RZ"]
_LOAD_COLUMNS = ["Nó", "Fx (N)", "Fy (N)", "Fz (N)", "Mx (N.mm)", "My (N.mm)", "Mz (N.mm)"]

_TRUE_VALUES = {"1", "true", "verdadeiro", "sim", "s", "x"}


class ModelInputError(ValueError):
    """Erro de entrada do usuario nas tabelas do modelo (mensagem ja pronta para exibir)."""


def _run_or_report[T](
    action: Callable[[], T],
    *,
    on_model_input_error: Callable[[str], None],
    on_other_error: Callable[[str], None],
) -> T | None:
    """Executa ``action``; se levantar ``ModelInputError`` ou qualquer
    outra excecao, reporta a mensagem via o callback correspondente e
    devolve ``None`` em vez de propagar.

    Compartilhado por ``ModelTab._on_run_analysis`` e
    ``Viewport3D._on_refresh`` (``openstruct.gui.viewport_3d``) — os
    dois precisam montar o modelo a partir das tabelas e mostrar um
    erro sem crashar; so decidem COMO exibir esse erro (dialogo modal
    vs rotulo de status), nao como classifica-lo.
    """
    try:
        return action()
    except ModelInputError as exc:
        on_model_input_error(str(exc))
    except Exception as exc:  # noqa: BLE001 - qualquer falha vira mensagem para o chamador
        on_other_error(str(exc))
    return None


def _parse_float(text: str, *, field: str, table: str, row: int) -> float:
    try:
        return parse_decimal(text)
    except ValueError as exc:
        raise ModelInputError(
            f"{table}, linha {row + 1}: campo '{field}' deve ser um numero, recebido {text!r}."
        ) from exc


def _parse_int(text: str, *, field: str, table: str, row: int) -> int:
    try:
        return int(text)
    except ValueError as exc:
        raise ModelInputError(
            f"{table}, linha {row + 1}: campo '{field}' deve ser um numero inteiro, "
            f"recebido {text!r}."
        ) from exc


def _parse_bool(text: str) -> bool:
    return text.strip().lower() in _TRUE_VALUES


class ModelTab(QWidget):
    """Monta o modelo estrutural a partir de tabelas e roda a analise."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.nodes_table = EditableTable(_NODE_COLUMNS, self)
        self.materials_table = EditableTable(_MATERIAL_COLUMNS, self)
        self.sections_table = EditableTable(_SECTION_COLUMNS, self)
        self.elements_table = EditableTable(_ELEMENT_COLUMNS, self)
        self.supports_table = EditableTable(_SUPPORT_COLUMNS, self)
        self.loads_table = EditableTable(_LOAD_COLUMNS, self)

        self.self_weight_checkbox = QCheckBox(
            "Incluir peso próprio automaticamente (gravidade = 9,81 m/s² em -Z, "
            "ver self_weight_loads)",
            self,
        )

        self.run_button = QPushButton("Rodar Análise", self)
        self.run_button.clicked.connect(self._on_run_analysis)

        self.results_tabs = QTabWidget(self)
        self.displacements_table = self._make_result_table(
            ["Nó", "UX (mm)", "UY (mm)", "UZ (mm)", "RX (rad)", "RY (rad)", "RZ (rad)"]
        )
        self.reactions_table = self._make_result_table(
            ["Nó", "Fx (N)", "Fy (N)", "Fz (N)", "Mx (N.mm)", "My (N.mm)", "Mz (N.mm)"]
        )
        self.element_forces_table = self._make_result_table(
            [
                "Elemento",
                "N_i (N)", "Vy_i (N)", "Vz_i (N)", "T_i (N.mm)", "My_i (N.mm)", "Mz_i (N.mm)",
                "N_j (N)", "Vy_j (N)", "Vz_j (N)", "T_j (N.mm)", "My_j (N.mm)", "Mz_j (N.mm)",
            ]
        )
        self.results_tabs.addTab(self.displacements_table, "Deslocamentos")
        self.results_tabs.addTab(self.reactions_table, "Reações")
        self.results_tabs.addTab(self.element_forces_table, "Esforços internos (eixos locais)")

        top = QSplitter(self)
        top.setOrientation(Qt.Orientation.Vertical)
        for label, widget in (
            ("Nós", self.nodes_table),
            ("Materiais", self.materials_table),
            ("Seções", self.sections_table),
            ("Elementos", self.elements_table),
            ("Apoios (marque os DOFs restringidos, ex.: 1/true/x)", self.supports_table),
            ("Cargas nodais", self.loads_table),
        ):
            container = QWidget(self)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(QLabel(f"<b>{label}</b>", self))
            container_layout.addWidget(widget)
            top.addWidget(container)

        layout = QVBoxLayout(self)
        layout.addWidget(top, stretch=3)
        layout.addWidget(self.self_weight_checkbox)
        layout.addWidget(self.run_button)
        layout.addWidget(QLabel("<b>Resultados</b>", self))
        layout.addWidget(self.results_tabs, stretch=2)

        # Cache da ultima analise bem-sucedida, consumido pela aba
        # "Visualizacao 3D" (viewport_3d.Viewport3D) para sobrepor a forma
        # deformada sem precisar re-executar a analise nem duplicar
        # nenhuma logica de montagem/solucao aqui. `_last_tables_snapshot`
        # guarda o estado das tabelas NO MOMENTO dessa analise — usado por
        # `is_last_result_stale()` para o viewport recusar sobrepor uma
        # deformada que nao corresponde mais ao modelo/cargas atuais
        # (tabelas editadas apos "Rodar Analise" sem rodar de novo).
        self.last_result: AnalysisResult | None = None
        self._last_tables_snapshot: tuple[object, ...] = ()

    @staticmethod
    def _make_result_table(columns: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return table

    # -- construcao do modelo a partir das tabelas ------------------------------

    def build_model_and_load_case(self) -> tuple[AnalysisModel, LoadCase]:
        """Le as tabelas e monta ``AnalysisModel``/``LoadCase`` — levanta
        ``ModelInputError`` com uma mensagem pronta para exibir se algo
        estiver invalido ou incompleto."""
        model = AnalysisModel()

        for row, values in enumerate(self.nodes_table.all_rows()):
            id_text, x_text, y_text, z_text = values
            node = Node(
                _parse_int(id_text, field="ID", table="Nós", row=row),
                _parse_float(x_text, field="X", table="Nós", row=row),
                _parse_float(y_text, field="Y", table="Nós", row=row),
                _parse_float(z_text, field="Z", table="Nós", row=row),
            )
            model.add_node(node)

        materials: dict[str, Material] = {}
        for row, values in enumerate(self.materials_table.all_rows()):
            name, e_text, g_text, density_text, fy_text, fu_text, poisson_text = values
            if not name:
                raise ModelInputError(f"Materiais, linha {row + 1}: 'Nome' não pode ser vazio.")
            if name in materials:
                raise ModelInputError(
                    f"Materiais, linha {row + 1}: nome {name!r} já usado em outra linha "
                    "— nomes de material devem ser únicos."
                )
            materials[name] = Material(
                name=name,
                E=_parse_float(e_text, field="E", table="Materiais", row=row),
                G=_parse_float(g_text, field="G", table="Materiais", row=row),
                density=_parse_float(density_text, field="density", table="Materiais", row=row),
                fy=_parse_float(fy_text, field="fy", table="Materiais", row=row),
                fu=_parse_float(fu_text, field="fu", table="Materiais", row=row),
                poisson=_parse_float(poisson_text, field="poisson", table="Materiais", row=row),
            )

        sections: dict[str, Section] = {}
        for row, values in enumerate(self.sections_table.all_rows()):
            (
                name, a_text, iy_text, iz_text, j_text,
                wply_text, wplz_text, wely_text, welz_text, cw_text,
            ) = values
            if not name:
                raise ModelInputError(f"Seções, linha {row + 1}: 'Nome' não pode ser vazio.")
            if name in sections:
                raise ModelInputError(
                    f"Seções, linha {row + 1}: nome {name!r} já usado em outra linha "
                    "— nomes de seção devem ser únicos."
                )
            sections[name] = Section(
                name=name,
                A=_parse_float(a_text, field="A", table="Seções", row=row),
                Iy=_parse_float(iy_text, field="Iy", table="Seções", row=row),
                Iz=_parse_float(iz_text, field="Iz", table="Seções", row=row),
                J=_parse_float(j_text, field="J", table="Seções", row=row),
                Wply=_parse_float(wply_text, field="Wply", table="Seções", row=row),
                Wplz=_parse_float(wplz_text, field="Wplz", table="Seções", row=row),
                Wely=_parse_float(wely_text, field="Wely", table="Seções", row=row),
                Welz=_parse_float(welz_text, field="Welz", table="Seções", row=row),
                Cw=_parse_float(cw_text, field="Cw", table="Seções", row=row) if cw_text else None,
            )

        for row, values in enumerate(self.elements_table.all_rows()):
            id_text, node_i_text, node_j_text, material_name, section_name = values
            element_id = _parse_int(id_text, field="ID", table="Elementos", row=row)
            node_i_id = _parse_int(node_i_text, field="Nó I", table="Elementos", row=row)
            node_j_id = _parse_int(node_j_text, field="Nó J", table="Elementos", row=row)
            if node_i_id not in model.nodes or node_j_id not in model.nodes:
                raise ModelInputError(
                    f"Elementos, linha {row + 1}: nó {node_i_id} ou {node_j_id} não existe "
                    "na tabela de Nós."
                )
            if material_name not in materials:
                raise ModelInputError(
                    f"Elementos, linha {row + 1}: material {material_name!r} não existe "
                    "na tabela de Materiais."
                )
            if section_name not in sections:
                raise ModelInputError(
                    f"Elementos, linha {row + 1}: seção {section_name!r} não existe "
                    "na tabela de Seções."
                )
            model.add_element(
                Element3D(
                    element_id,
                    (model.nodes[node_i_id], model.nodes[node_j_id]),
                    materials[material_name],
                    sections[section_name],
                )
            )

        for row, values in enumerate(self.supports_table.all_rows()):
            node_text, ux, uy, uz, rx, ry, rz = values
            node_id = _parse_int(node_text, field="Nó", table="Apoios", row=row)
            if node_id not in model.nodes:
                raise ModelInputError(
                    f"Apoios, linha {row + 1}: nó {node_id} não existe na tabela de Nós."
                )
            model.add_support(
                Support(
                    node_id,
                    ux=_parse_bool(ux),
                    uy=_parse_bool(uy),
                    uz=_parse_bool(uz),
                    rx=_parse_bool(rx),
                    ry=_parse_bool(ry),
                    rz=_parse_bool(rz),
                )
            )

        nodal_loads = []
        for row, values in enumerate(self.loads_table.all_rows()):
            node_text, fx, fy, fz, mx, my, mz = values
            node_id = _parse_int(node_text, field="Nó", table="Cargas", row=row)
            if node_id not in model.nodes:
                raise ModelInputError(
                    f"Cargas, linha {row + 1}: nó {node_id} não existe na tabela de Nós."
                )
            nodal_loads.append(
                NodalLoad(
                    node_id,
                    fx=_parse_float(fx, field="Fx", table="Cargas", row=row),
                    fy=_parse_float(fy, field="Fy", table="Cargas", row=row),
                    fz=_parse_float(fz, field="Fz", table="Cargas", row=row),
                    mx=_parse_float(mx, field="Mx", table="Cargas", row=row),
                    my=_parse_float(my, field="My", table="Cargas", row=row),
                    mz=_parse_float(mz, field="Mz", table="Cargas", row=row),
                )
            )

        element_loads: tuple[ElementLoad, ...] = ()
        if self.self_weight_checkbox.isChecked():
            element_loads = self_weight_loads(model)  # gravity=9,81 m/s² (DEFAULT_GRAVITY)

        load_case = LoadCase("Caso GUI", tuple(nodal_loads), element_loads)
        return model, load_case

    # -- execucao e exibicao de resultados --------------------------------------

    def _tables_snapshot(self) -> tuple[object, ...]:
        """Retrato do estado bruto de todas as tabelas + checkbox de peso
        proprio — usado para detectar se ``last_result`` ficou desatualizado
        em relacao ao que esta nas tabelas agora (ver ``is_last_result_stale``)."""
        return (
            self.nodes_table.all_rows(),
            self.materials_table.all_rows(),
            self.sections_table.all_rows(),
            self.elements_table.all_rows(),
            self.supports_table.all_rows(),
            self.loads_table.all_rows(),
            self.self_weight_checkbox.isChecked(),
        )

    def is_last_result_stale(self) -> bool:
        """``True`` se ``last_result`` for ``None`` ou se qualquer tabela
        (ou o checkbox de peso proprio) tiver mudado desde a ultima
        execucao bem-sucedida de ``Rodar Analise`` — consumido pela aba
        "Visualizacao 3D" para nao sobrepor uma forma deformada que nao
        corresponde mais ao modelo/cargas atuais."""
        return self.last_result is None or self._tables_snapshot() != self._last_tables_snapshot

    def _run_full_analysis(self) -> AnalysisResult:
        model, load_case = self.build_model_and_load_case()
        return run_analysis(model, load_case)

    def _show_model_input_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro nos dados do modelo", message)

    def _show_analysis_error(self, message: str) -> None:
        QMessageBox.critical(self, "Erro ao rodar a análise", message)

    def _on_run_analysis(self) -> None:
        result = _run_or_report(
            self._run_full_analysis,
            on_model_input_error=self._show_model_input_error,
            on_other_error=self._show_analysis_error,
        )
        if result is None:
            return
        self.last_result = result
        self._last_tables_snapshot = self._tables_snapshot()
        self._show_results(result)

    def _show_results(self, result: AnalysisResult) -> None:
        self.displacements_table.setRowCount(0)
        for node_id, values in sorted(result.displacements.items()):
            row = self.displacements_table.rowCount()
            self.displacements_table.insertRow(row)
            self.displacements_table.setItem(row, 0, QTableWidgetItem(str(node_id)))
            for col, value in enumerate(values, start=1):
                self.displacements_table.setItem(row, col, QTableWidgetItem(f"{value:.6g}"))

        self.reactions_table.setRowCount(0)
        for node_id, values in sorted(result.reactions.items()):
            row = self.reactions_table.rowCount()
            self.reactions_table.insertRow(row)
            self.reactions_table.setItem(row, 0, QTableWidgetItem(str(node_id)))
            for col, value in enumerate(values, start=1):
                self.reactions_table.setItem(row, col, QTableWidgetItem(f"{value:.6g}"))

        self.element_forces_table.setRowCount(0)
        for element_id, values in sorted(result.element_forces.items()):
            row = self.element_forces_table.rowCount()
            self.element_forces_table.insertRow(row)
            self.element_forces_table.setItem(row, 0, QTableWidgetItem(str(element_id)))
            for col, value in enumerate(values, start=1):
                self.element_forces_table.setItem(row, col, QTableWidgetItem(f"{value:.6g}"))
