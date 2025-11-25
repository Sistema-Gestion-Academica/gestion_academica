"""Modelo de dominio para administrador."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .usuario import Usuario


@dataclass
class Administrador(Usuario):
    def crearPlan(self, nombre: str, descripcion: str) -> "Plan":
        from ..plan import Plan

        return Plan(id=None, nombre=nombre, descripcion=descripcion, materias=[])

    def crearMateria(
        self,
        nombre: str,
        codigo: str,
        descripcion: str,
        correlativas: Optional[List[str]] = None,
    ) -> "Materia":
        from ..materia import Materia

        return Materia(
            id=None,
            nombre=nombre,
            codigo=codigo,
            descripcion=descripcion or "",
            correlativas=list(correlativas or []),
        )

    def crearCohorte(
        self, nombre: str, plan_id: str, alumnos_ids: Optional[List[str]] = None
    ) -> "Cohorte":
        from ..cohorte import Cohorte

        return Cohorte(
            id=None, nombre=nombre, plan_id=plan_id, alumnos=list(alumnos_ids or [])
        )

    def crearCurso(
        self,
        nombre: str,
        materia_id: str,
        cohorte_id: Optional[str] = None,
        docente_id: Optional[str] = None,
    ) -> "Curso":
        from ..curso import Curso

        return Curso(
            id=None,
            nombre=nombre,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            docente_id=docente_id,
        )

    def asignarDocente(self, curso: "Curso", docente_id: str) -> "Curso":
        curso.docente_id = docente_id
        return curso
