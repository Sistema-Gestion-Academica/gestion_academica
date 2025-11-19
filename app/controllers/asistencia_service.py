"""Servicio compartido para los flujos de asistencia."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Set

from app.models.asistencia import Asistencia
from app.models.dbbroker import DBBroker


class AsistenciaService:
    def __init__(self, broker: Optional[DBBroker] = None) -> None:
        self.broker = broker or DBBroker()

    def registrarAsistencia(self, usuario_id: str, rol: str, presente: bool, fecha_registro: Optional[str] = None) -> Asistencia:
        fecha = fecha_registro or date.today().isoformat()
        if self._existe_asistencia(usuario_id, rol, fecha):
            raise ValueError("Asistencia ya registrada para hoy")
        registro = Asistencia(
            id=None,
            usuario_id=usuario_id,
            fecha=fecha,
            presente=presente,
            rol=rol,
        )
        self.broker.guardarObjeto(registro)
        return registro

    def consultarAsistencia(self, usuario_id: str, rol: str, mes: Optional[str] = None) -> Dict[str, object]:
        registros = [
            Asistencia.from_dict(item)
            for item in self.broker.listar("Asistencia")
            if item.get("usuario_id") == usuario_id and item.get("rol") == rol
        ]
        target_month = self._parse_month(mes)
        month_start = date(target_month.year, target_month.month, 1)
        last_day = monthrange(target_month.year, target_month.month)[1]
        month_end = date(target_month.year, target_month.month, last_day)
        today = date.today()
        effective_end = min(month_end, today)

        registros_mes = [
            registro
            for registro in registros
            if self._is_in_month(registro.fecha, target_month.year, target_month.month)
        ]
        present_dates = {registro.fecha for registro in registros_mes if registro.presente}
        expected_total = self._count_weekdays(month_start, effective_end)
        resumen = self._resumen(registros_mes, expected_total)
        calendar_days = self._build_calendar(month_start, present_dates)
        registros_ordenados = sorted(registros, key=lambda r: r.fecha, reverse=True)
        return {
            "registros_mes": sorted(registros_mes, key=lambda r: r.fecha, reverse=True),
            "registros": registros_ordenados,
            "resumen": resumen,
            "mes": target_month.strftime("%Y-%m"),
            "mes_label": self._label_mes(target_month.year, target_month.month),
            "dias_presentes": present_dates,
            "calendar_days": calendar_days,
        }

    def _resumen(self, registros: List[Asistencia], esperado: int) -> Dict[str, float]:
        presentes = len([r for r in registros if r.presente])
        porcentaje = Asistencia.CalcularPorcentaje({"total": esperado, "present": presentes})
        return {"total": float(esperado), "presentes": float(presentes), "porcentaje": porcentaje}

    def _existe_asistencia(self, usuario_id: str, rol: str, fecha: str) -> bool:
        return any(
            item.get("usuario_id") == usuario_id and item.get("rol") == rol and item.get("fecha") == fecha
            for item in self.broker.listar("Asistencia")
        )

    def _parse_month(self, mes: Optional[str]) -> date:
        if mes:
            try:
                parsed = datetime.strptime(mes, "%Y-%m")
                return parsed.date()
            except ValueError:
                pass
        return date.today()

    def _is_in_month(self, fecha_iso: str, year: int, month: int) -> bool:
        try:
            dt = datetime.fromisoformat(fecha_iso).date()
        except ValueError:
            return False
        return dt.year == year and dt.month == month

    def _build_calendar(self, month_start: date, present_dates: Set[str]) -> List[Dict[str, object]]:
        first_weekday, days_in_month = monthrange(month_start.year, month_start.month)
        days: List[Dict[str, object]] = []
        present_lookup = set(present_dates)
        today = date.today()

        for _ in range(first_weekday):
            days.append(self._empty_day())

        for day in range(1, days_in_month + 1):
            current_date = date(month_start.year, month_start.month, day)
            iso = current_date.isoformat()
            days.append(
                {
                    "label": day,
                    "iso": iso,
                    "is_current_month": True,
                    "is_today": current_date == today,
                    "is_present": iso in present_lookup,
                }
            )

        while len(days) % 7 != 0:
            days.append(self._empty_day())

        return days

    def _empty_day(self) -> Dict[str, object]:
        return {"label": "", "iso": None, "is_current_month": False, "is_today": False, "is_present": False}

    def _label_mes(self, year: int, month: int) -> str:
        meses = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
        nombre = meses[month - 1] if 1 <= month <= 12 else "mes"
        return f"{nombre.capitalize()} {year}"

    def _count_weekdays(self, start: date, end: date) -> int:
        if end < start:
            return 0
        total_days = (end - start).days + 1
        weekdays = 0
        for i in range(total_days):
            current = start + timedelta(days=i)
            if current.weekday() < 5:
                weekdays += 1
        return weekdays
