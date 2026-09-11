"""Aba "Verificações NBR 8800": um formulário por verificação implementada.

Camada fina sobre ``openstruct.normative.nbr8800`` — cada botão
"Verificar" desta aba chama diretamente a funcao ``check_*`` ja
implementada/validada correspondente (ver
``docs/normative/NBR8800-RULES.md``); nenhuma formula normativa e
reescrita aqui.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from openstruct.normative.nbr8800 import (
    LoadCombinationClass,
    check_axial_and_bending_interaction,
    check_compression_member,
    check_flexural_resistance_major_axis,
    check_shear_major_axis,
    check_tension_member,
    steel_resistance_factors,
)

from ._parsing import parse_decimal

_LOAD_COMBINATION_LABELS = {
    LoadCombinationClass.NORMAL: "Normal",
    LoadCombinationClass.ESPECIAL_OU_CONSTRUCAO: "Especial ou de construção",
    LoadCombinationClass.EXCEPCIONAL: "Excepcional",
}


class _CheckResultLike(Protocol):
    """Forma comum das ``*CheckResult`` de ``openstruct.normative.nbr8800``
    (``sd``/``rd``/``utilization``/``is_ok``) — um ``Protocol`` local em vez
    de importar a ABC privada ``_check_result.CheckResult`` (nao faz parte
    da API publica do pacote, ver seu modulo-docstring)."""

    @property
    def sd(self) -> float: ...
    @property
    def rd(self) -> float: ...
    @property
    def utilization(self) -> float: ...
    @property
    def is_ok(self) -> bool: ...


def _parse_float(text: str, field: str) -> float:
    try:
        return parse_decimal(text)
    except ValueError as exc:
        raise ValueError(f"Campo '{field}' deve ser um número, recebido {text!r}.") from exc


def _combination_combo() -> QComboBox:
    combo = QComboBox()
    for combination, label in _LOAD_COMBINATION_LABELS.items():
        combo.addItem(label, combination)
    return combo


def _combination_from_combo(combo: QComboBox) -> LoadCombinationClass:
    value = combo.currentData()
    assert isinstance(value, LoadCombinationClass)
    return value


class _CheckPage(QWidget):
    """Uma pagina de formulario + resultado, reutilizada pelas 5 verificacoes."""

    def __init__(
        self, fields: list[tuple[str, str, QWidget | None]], parent: QWidget | None = None
    ) -> None:
        """``fields``: lista de ``(rotulo, texto_padrao, widget_customizado)``.

        Se ``widget_customizado`` for ``None``, cria um ``QLineEdit``
        com ``texto_padrao`` (acessivel via :attr:`inputs`); caso
        contrario usa o widget dado (ex.: ``QComboBox``, ``QCheckBox``)
        e ``texto_padrao`` e ignorado.
        """
        super().__init__(parent)
        self.inputs: dict[str, QWidget] = {}
        form = QFormLayout()
        for label, default_text, custom_widget in fields:
            widget: QWidget
            if custom_widget is not None:
                widget = custom_widget
            else:
                widget = QLineEdit(default_text)
            self.inputs[label] = widget
            form.addRow(label, widget)

        self.run_button = QPushButton("Verificar")
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_label)

    def text(self, label: str) -> str:
        widget = self.inputs[label]
        assert isinstance(widget, QLineEdit)
        return widget.text()

    def combo(self, label: str) -> QComboBox:
        widget = self.inputs[label]
        assert isinstance(widget, QComboBox)
        return widget

    def checkbox(self, label: str) -> QCheckBox:
        widget = self.inputs[label]
        assert isinstance(widget, QCheckBox)
        return widget

    def show_result(self, result: _CheckResultLike, *, sd_label: str, rd_label: str) -> None:
        status = "✅ APROVADO" if result.is_ok else "❌ REPROVADO"
        self.result_label.setText(
            f"{status} — {sd_label}={result.sd:.6g}, {rd_label}={result.rd:.6g}, "
            f"utilização={result.utilization:.4f}"
        )

    def show_error(self, message: str) -> None:
        self.result_label.setText(f"⚠ Erro: {message}")


def _wrap_run(
    page: _CheckPage, compute: Callable[[], tuple[_CheckResultLike, str, str]]
) -> Callable[[], None]:
    def handler() -> None:
        try:
            result, sd_label, rd_label = compute()
        except ValueError as exc:
            page.show_error(str(exc))
            return
        page.show_result(result, sd_label=sd_label, rd_label=rd_label)

    return handler


class ChecksTab(QWidget):
    """Combo de selecao + uma pagina de formulario por verificacao NBR 8800."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.selector = QComboBox(self)
        self.stack = QStackedWidget(self)

        for title, page in (
            ("Tração (5.2)", self._build_tension_page()),
            ("Compressão — apenas flexão (5.3)", self._build_compression_page()),
            ("Cisalhamento, eixo maior (5.4.3.1)", self._build_shear_page()),
            ("Flexão completa, FLT+FLM+FLA (5.4.2/Anexo D)", self._build_flexure_page()),
            ("Combinação N+M biaxial (5.5.1.2)", self._build_combined_page()),
        ):
            self.selector.addItem(title)
            self.stack.addWidget(page)
        self.selector.currentIndexChanged.connect(self.stack.setCurrentIndex)

        layout = QVBoxLayout(self)
        layout.addWidget(self.selector)
        layout.addWidget(self.stack)
        layout.addStretch(1)

    # -- 5.2 traca --------------------------------------------------------------

    def _build_tension_page(self) -> _CheckPage:
        combination = _combination_combo()
        page = _CheckPage(
            [
                ("Nt,Sd — força axial de tração solicitante (N)", "100000", None),
                ("Ag — área bruta (mm²)", "2680", None),
                ("Ae — área líquida efetiva (mm²)", "2680", None),
                ("fy — tensão de escoamento (MPa)", "345", None),
                ("fu — tensão de ruptura (MPa)", "450", None),
                ("Classe de combinação", "", combination),
            ]
        )

        def compute() -> tuple[_CheckResultLike, str, str]:
            nt_sd = _parse_float(
                page.text("Nt,Sd — força axial de tração solicitante (N)"), "Nt,Sd"
            )
            ag = _parse_float(page.text("Ag — área bruta (mm²)"), "Ag")
            ae = _parse_float(page.text("Ae — área líquida efetiva (mm²)"), "Ae")
            fy = _parse_float(page.text("fy — tensão de escoamento (MPa)"), "fy")
            fu = _parse_float(page.text("fu — tensão de ruptura (MPa)"), "fu")
            factors = steel_resistance_factors(_combination_from_combo(combination))
            result = check_tension_member(nt_sd, ag, ae, fy, fu, factors)
            return result, "Nt,Sd", "Nt,Rd"

        page.run_button.clicked.connect(_wrap_run(page, compute))
        return page

    # -- 5.3 compressao (apenas flexao, ver ATENCAO em compression.py) ----------

    def _build_compression_page(self) -> _CheckPage:
        combination = _combination_combo()
        page = _CheckPage(
            [
                ("Nc,Sd — força axial de compressão solicitante (N)", "100000", None),
                ("Ag — área bruta (mm²)", "2680", None),
                ("Aef — área efetiva (mm², = Ag sem flambagem local)", "2680", None),
                ("fy — tensão de escoamento (MPa)", "345", None),
                (
                    "Ne — força axial de flambagem elástica governante, "
                    "min(Nex,Ney,Nez) (N)",
                    "467572.5",
                    None,
                ),
                ("Classe de combinação", "", combination),
            ]
        )

        def compute() -> tuple[_CheckResultLike, str, str]:
            nc_sd = _parse_float(
                page.text("Nc,Sd — força axial de compressão solicitante (N)"), "Nc,Sd"
            )
            ag = _parse_float(page.text("Ag — área bruta (mm²)"), "Ag")
            aef = _parse_float(
                page.text("Aef — área efetiva (mm², = Ag sem flambagem local)"), "Aef"
            )
            fy = _parse_float(page.text("fy — tensão de escoamento (MPa)"), "fy")
            ne = _parse_float(
                page.text(
                    "Ne — força axial de flambagem elástica governante, min(Nex,Ney,Nez) (N)"
                ),
                "Ne",
            )
            factors = steel_resistance_factors(_combination_from_combo(combination))
            result = check_compression_member(nc_sd, ag, aef, fy, ne, factors)
            return result, "Nc,Sd", "Nc,Rd"

        page.run_button.clicked.connect(_wrap_run(page, compute))
        return page

    # -- 5.4.3.1 cisalhamento ----------------------------------------------------

    def _build_shear_page(self) -> _CheckPage:
        page = _CheckPage(
            [
                ("Vsd — força cortante solicitante (N)", "100000", None),
                ("d — altura total da seção (mm)", "400", None),
                ("h — altura livre da alma (mm)", "350", None),
                ("tw — espessura da alma (mm)", "8", None),
                ("fy — tensão de escoamento (MPa)", "345", None),
                ("E — módulo de elasticidade (MPa)", "200000", None),
                ("a — espaçamento entre enrijecedores (mm, vazio = sem enrijecedores)", "", None),
                ("γa1", "1.10", None),
            ]
        )

        def compute() -> tuple[_CheckResultLike, str, str]:
            vsd = _parse_float(page.text("Vsd — força cortante solicitante (N)"), "Vsd")
            d = _parse_float(page.text("d — altura total da seção (mm)"), "d")
            h = _parse_float(page.text("h — altura livre da alma (mm)"), "h")
            tw = _parse_float(page.text("tw — espessura da alma (mm)"), "tw")
            fy = _parse_float(page.text("fy — tensão de escoamento (MPa)"), "fy")
            e = _parse_float(page.text("E — módulo de elasticidade (MPa)"), "E")
            a_text = page.text(
                "a — espaçamento entre enrijecedores (mm, vazio = sem enrijecedores)"
            )
            a = _parse_float(a_text, "a") if a_text else None
            gamma_a1 = _parse_float(page.text("γa1"), "γa1")
            result = check_shear_major_axis(vsd, d, h, tw, fy, e, a, gamma_a1)
            return result, "Vsd", "Vrd"

        page.run_button.clicked.connect(_wrap_run(page, compute))
        return page

    # -- 5.4.2/Anexo D flexao completa -------------------------------------------

    def _build_flexure_page(self) -> _CheckPage:
        rolled_checkbox = QCheckBox("Perfil laminado (desmarcado = soldado)")
        rolled_checkbox.setChecked(True)
        page = _CheckPage(
            [
                ("Msd — momento fletor solicitante, MAGNITUDE (N.mm)", "100000000", None),
                ("fy — tensão de escoamento (MPa)", "345", None),
                ("E — módulo de elasticidade (MPa)", "200000", None),
                ("W — módulo de resistência elástico, eixo de flexão (mm³)", "900000", None),
                ("Z — módulo de resistência plástico, eixo de flexão (mm³)", "1000000", None),
                ("Iy — momento de inércia, eixo menor (mm⁴)", "20000000", None),
                ("J — constante de torção (mm⁴)", "500000", None),
                ("Cw — constante de empenamento (mm⁶)", "737280000000", None),
                ("ry — raio de giração, eixo menor (mm)", "60", None),
                ("Lb — comprimento destravado (mm)", "1500", None),
                ("Cb — fator de modificação (1,0 = conservador)", "1.0", None),
                ("bf — largura total da mesa (mm)", "200", None),
                ("tf — espessura da mesa (mm)", "16", None),
                ("h — altura livre da alma (mm)", "350", None),
                ("tw — espessura da alma (mm)", "8", None),
                ("Perfil", "", rolled_checkbox),
                ("γa1", "1.10", None),
            ]
        )

        def compute() -> tuple[_CheckResultLike, str, str]:
            msd = _parse_float(
                page.text("Msd — momento fletor solicitante, MAGNITUDE (N.mm)"), "Msd"
            )
            fy = _parse_float(page.text("fy — tensão de escoamento (MPa)"), "fy")
            e = _parse_float(page.text("E — módulo de elasticidade (MPa)"), "E")
            w = _parse_float(
                page.text("W — módulo de resistência elástico, eixo de flexão (mm³)"), "W"
            )
            z = _parse_float(
                page.text("Z — módulo de resistência plástico, eixo de flexão (mm³)"), "Z"
            )
            iy = _parse_float(page.text("Iy — momento de inércia, eixo menor (mm⁴)"), "Iy")
            j = _parse_float(page.text("J — constante de torção (mm⁴)"), "J")
            cw = _parse_float(page.text("Cw — constante de empenamento (mm⁶)"), "Cw")
            ry = _parse_float(page.text("ry — raio de giração, eixo menor (mm)"), "ry")
            lb = _parse_float(page.text("Lb — comprimento destravado (mm)"), "Lb")
            cb = _parse_float(page.text("Cb — fator de modificação (1,0 = conservador)"), "Cb")
            bf = _parse_float(page.text("bf — largura total da mesa (mm)"), "bf")
            tf = _parse_float(page.text("tf — espessura da mesa (mm)"), "tf")
            h = _parse_float(page.text("h — altura livre da alma (mm)"), "h")
            tw = _parse_float(page.text("tw — espessura da alma (mm)"), "tw")
            rolled = rolled_checkbox.isChecked()
            gamma_a1 = _parse_float(page.text("γa1"), "γa1")
            result = check_flexural_resistance_major_axis(
                msd, fy, e, w, z, iy, j, cw, ry, lb, cb, bf, tf, h, tw, rolled, gamma_a1
            )
            return result, "Msd", "Mrd"

        page.run_button.clicked.connect(_wrap_run(page, compute))
        return page

    # -- 5.5.1.2 combinacao N+M ---------------------------------------------------

    def _build_combined_page(self) -> _CheckPage:
        page = _CheckPage(
            [
                ("Nsd — força axial solicitante, MAGNITUDE (N)", "300000", None),
                ("Nrd — força axial resistente correspondente (N)", "800000", None),
                ("Mx,sd — momento fletor solicitante em x, MAGNITUDE (N.mm)", "80000000", None),
                ("Mx,rd — momento fletor resistente em x (N.mm)", "300000000", None),
                ("My,sd — momento fletor solicitante em y, MAGNITUDE (N.mm)", "15000000", None),
                ("My,rd — momento fletor resistente em y (N.mm)", "80000000", None),
            ]
        )

        def compute() -> tuple[_CheckResultLike, str, str]:
            n_sd = _parse_float(page.text("Nsd — força axial solicitante, MAGNITUDE (N)"), "Nsd")
            n_rd = _parse_float(
                page.text("Nrd — força axial resistente correspondente (N)"), "Nrd"
            )
            mx_sd = _parse_float(
                page.text("Mx,sd — momento fletor solicitante em x, MAGNITUDE (N.mm)"), "Mx,sd"
            )
            mx_rd = _parse_float(
                page.text("Mx,rd — momento fletor resistente em x (N.mm)"), "Mx,rd"
            )
            my_sd = _parse_float(
                page.text("My,sd — momento fletor solicitante em y, MAGNITUDE (N.mm)"), "My,sd"
            )
            my_rd = _parse_float(
                page.text("My,rd — momento fletor resistente em y (N.mm)"), "My,rd"
            )
            result = check_axial_and_bending_interaction(n_sd, n_rd, mx_sd, mx_rd, my_sd, my_rd)
            return result, "razão de interação", "limite"

        page.run_button.clicked.connect(_wrap_run(page, compute))
        return page
