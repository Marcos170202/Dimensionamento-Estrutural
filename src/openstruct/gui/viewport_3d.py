"""Aba "Visualização 3D": desenha o modelo estrutural e, quando
disponível, a forma deformada da última análise executada.

Camada FINA sobre ``openstruct.domain``/``openstruct.results`` (PyVista/
VTK) — este módulo só converte coordenadas de nós, conectividade de
elementos e deslocamentos JÁ CALCULADOS em geometria para desenhar;
nenhuma fórmula de engenharia ou lógica de montagem de modelo mora
aqui. A montagem do modelo continua sendo feita por
``ModelTab.build_model_and_load_case`` — reaproveitada sem duplicação
(o botão "Atualizar visualização" desta aba chama exatamente essa
função).

Sem edição interativa nesta fase (criar/mover nó clicando no viewport,
mover elemento, atribuir material/seção/apoio/carga pelo desenho —
PROGRAM_MASTER.md seção 17, "MODELAGEM 3D"). O próprio PROGRAM_MASTER
marca essas operações como "Futuramente"; ficam para uma fase seguinte
(ver ``docs/decisions/ADR-004-viewport-3d.md``, seção "Fora do escopo").
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from numpy.typing import NDArray
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from openstruct.domain import AnalysisModel, LoadCase, NodalLoad
from openstruct.results import AnalysisResult

from .model_tab import ModelTab, _run_or_report

_STRUCTURE_COLOR = "steelblue"
_NODE_COLOR = "steelblue"
_SUPPORT_COLOR = "black"
_LOAD_COLOR = "darkorange"
_DEFORMED_COLOR = "crimson"

# Comprimento visual (NAO fisico) das setas de carga, como fracao da
# maior diagonal da caixa delimitadora do modelo — a magnitude real de
# uma forca em N pode variar em ordens de grandeza entre um modelo e
# outro, entao a seta e desenhada com um tamanho legivel, nao
# proporcional a intensidade (documentado no rotulo da interface).
_LOAD_ARROW_FRACTION = 0.15


def _bounding_diagonal(points: NDArray[np.float64]) -> float:
    """Diagonal da caixa delimitadora de ``points`` (>= 1.0 mm, evita seta de comprimento zero)."""
    if len(points) == 0:
        return 1.0
    diagonal = float(np.linalg.norm(points.max(axis=0) - points.min(axis=0)))
    return diagonal if diagonal > 1e-9 else 1.0


def _lines_polydata(
    points: NDArray[np.float64], connectivity: list[tuple[int, int]]
) -> pv.PolyData:
    """``PolyData`` de segmentos de reta ligando pares de índices em ``points``."""
    if not connectivity:
        return pv.PolyData(points)
    lines = np.hstack([[2, i, j] for i, j in connectivity])
    return pv.PolyData(points, lines=lines)


class Viewport3D(QWidget):
    """Viewport 3D (PyVista/VTK) do modelo montado em ``model_tab``."""

    def __init__(self, model_tab: ModelTab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model_tab = model_tab

        self.plotter = QtInteractor(self)

        self.refresh_button = QPushButton("Atualizar visualização", self)
        self.refresh_button.clicked.connect(self._on_refresh)

        self.show_deformed_checkbox = QCheckBox(
            "Mostrar forma deformada (referente à última análise executada"
            " em \"Modelo e Análise\")",
            self,
        )

        self.scale_spinbox = QDoubleSpinBox(self)
        self.scale_spinbox.setRange(0.0, 1_000_000.0)
        self.scale_spinbox.setDecimals(2)
        self.scale_spinbox.setValue(1.0)
        self.scale_spinbox.setToolTip(
            "Fator de ampliação dos deslocamentos no desenho — deslocamentos"
            " reais (mm) costumam ser pequenos demais para aparecer na escala"
            " da estrutura; aumente este valor para tornar a deformada visível."
        )

        self.status_label = QLabel("", self)
        self.status_label.setWordWrap(True)

        controls = QFormLayout()
        controls.addRow(self.refresh_button)
        controls.addRow(self.show_deformed_checkbox)
        controls.addRow("Fator de escala da deformada", self.scale_spinbox)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.plotter.interactor, stretch=1)
        layout.addWidget(self.status_label)

    def show_error(self, message: str) -> None:
        self.status_label.setText(f"⚠ Erro: {message}")

    # -- atualizacao a partir da aba "Modelo e Analise" --------------------------

    def _on_refresh(self) -> None:
        built = _run_or_report(
            self.model_tab.build_model_and_load_case,
            on_model_input_error=self.show_error,
            on_other_error=self.show_error,
        )
        if built is None:
            return
        model, load_case = built

        result = self.model_tab.last_result
        wants_deformed = self.show_deformed_checkbox.isChecked()
        if wants_deformed and result is not None and self.model_tab.is_last_result_stale():
            # As tabelas mudaram desde a ultima analise bem-sucedida — a
            # deformada cacheada NAO corresponde mais ao modelo/cargas
            # atuais. Melhor recusar a sobreposicao (mostrar so a estrutura
            # nao-deformada) do que desenhar uma deformada enganosa numa
            # ferramenta de engenharia estrutural.
            self.render_model(model, load_case, None)
            self.status_label.setText(
                "⚠ Forma deformada NÃO desenhada: as tabelas mudaram desde a"
                ' última execução de "Rodar Análise" — rode a análise'
                " novamente para uma deformada atualizada."
            )
            return
        self.render_model(model, load_case, result)

    # -- renderizacao --------------------------------------------------------------

    def render_model(
        self,
        model: AnalysisModel,
        load_case: LoadCase | None = None,
        result: AnalysisResult | None = None,
    ) -> None:
        """Redesenha o viewport a partir de ``model`` e, opcionalmente,
        das cargas de ``load_case`` e da forma deformada de ``result``."""
        self.status_label.setText("")
        self.plotter.clear()

        node_ids = sorted(model.nodes)
        if not node_ids:
            self.plotter.render()
            return

        index_of = {node_id: i for i, node_id in enumerate(node_ids)}
        points = np.array(
            [[model.nodes[nid].x, model.nodes[nid].y, model.nodes[nid].z] for nid in node_ids]
        )
        connectivity = [
            (index_of[element.nodes[0].id], index_of[element.nodes[1].id])
            for element in model.elements.values()
        ]

        self.plotter.add_mesh(
            _lines_polydata(points, connectivity), color=_STRUCTURE_COLOR, line_width=3
        )
        self.plotter.add_points(
            pv.PolyData(points), color=_NODE_COLOR, point_size=10, render_points_as_spheres=True
        )

        support_points = np.array(
            [
                [model.nodes[nid].x, model.nodes[nid].y, model.nodes[nid].z]
                for nid in node_ids
                if nid in model.supports
            ]
        )
        if len(support_points) > 0:
            self.plotter.add_points(
                pv.PolyData(support_points),
                color=_SUPPORT_COLOR,
                point_size=16,
                render_points_as_spheres=True,
            )

        if load_case is not None:
            self._add_load_arrows(load_case, model, _bounding_diagonal(points))

        if result is not None and self.show_deformed_checkbox.isChecked():
            self._add_deformed_shape(points, connectivity, node_ids, result)

        # mypy ve `reset_camera` como um `functools._Wrapped` mal-tipado
        # (limitacao conhecida dos stubs do PyVista para metodos delegados
        # via decorador entre BasePlotter/Renderer) — chamada sem argumentos
        # funciona normalmente em runtime (confirmado por smoke test).
        self.plotter.reset_camera()  # type: ignore[call-arg]
        self.plotter.render()

    def _add_load_arrows(
        self, load_case: LoadCase, model: AnalysisModel, diagonal: float
    ) -> None:
        """Desenha uma seta por ``NodalLoad`` com força não nula.

        Momentos (``mx``/``my``/``mz``) NÃO são desenhados nesta fase —
        ver ``docs/decisions/ADR-004-viewport-3d.md``, "Fora do escopo".
        """
        arrow_length = diagonal * _LOAD_ARROW_FRACTION
        for load in load_case.loads:
            # `Load` (ABC) so tem `NodalLoad` como subclasse concreta hoje
            # (ver openstruct.domain.loads) — guarda defensiva para um
            # futuro tipo de carga direta em no, nunca exercitada agora.
            if not isinstance(load, NodalLoad):
                continue  # pragma: no cover
            force = np.array([load.fx, load.fy, load.fz])
            magnitude = float(np.linalg.norm(force))
            if magnitude < 1e-9 or load.node_id not in model.nodes:
                continue
            direction = force / magnitude
            node = model.nodes[load.node_id]
            tip = np.array([node.x, node.y, node.z])
            start = tip - direction * arrow_length
            arrow = pv.Arrow(start=start, direction=direction, scale=arrow_length)
            self.plotter.add_mesh(arrow, color=_LOAD_COLOR)

    def _add_deformed_shape(
        self,
        points: NDArray[np.float64],
        connectivity: list[tuple[int, int]],
        node_ids: list[int],
        result: AnalysisResult,
    ) -> None:
        """Sobrepõe a estrutura deslocada (translações nodais × fator de escala).

        Aproximação de desenho: liga as posições NODAIS deslocadas por
        segmentos de reta — não usa as funções de forma de Hermite do
        elemento para a curvatura real entre nós (isso exigiria
        reamostrar o campo de deslocamento ao longo do vão, fora do
        escopo desta fase; ver ADR-004).
        """
        scale = self.scale_spinbox.value()
        displaced = points.copy()
        for i, node_id in enumerate(node_ids):
            if node_id in result.displacements:
                ux, uy, uz, _rx, _ry, _rz = result.displacements[node_id]
                displaced[i] += np.array([ux, uy, uz]) * scale
        self.plotter.add_mesh(
            _lines_polydata(displaced, connectivity),
            color=_DEFORMED_COLOR,
            line_width=2,
            style="wireframe",
        )
