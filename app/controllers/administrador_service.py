

from __future__ import annotations

from typing import List, Optional

from app.models.USRs import Administrador, Alumno, Docente
from app.models.cohorte import Cohorte
from app.models.curso import Curso
from app.models.dbbroker import DBBroker
from app.models.examen import Examen
from app.models.materia import Materia
from app.models.plan import Plan


class AdministradorService:
    def __init__(self, broker: Optional[DBBroker] = None) -> None:
        self.broker = broker or DBBroker()

    def crearMateria(
        self,
        admin: Administrador,
        nombre: str,
        codigo: str,
        descripcion: Optional[str],
        correlativas: Optional[List[str]] = None,
    ) -> Materia:
        correlativas_limpias = [value for value in (correlativas or []) if value]
        materia = admin.crearMateria(nombre, codigo, descripcion or "", correlativas_limpias)
        self.broker.guardarObjeto(materia)
        return materia

    def obtenerMateria(self, materia_id: str) -> Materia:
        data = self.broker.obtenerPorId("Materia", materia_id)
        if not data:
            raise ValueError("Materia no encontrada")
        return Materia.from_dict(data)

    def actualizarMateria(
        self,
        materia_id: str,
        nombre: str,
        codigo: str,
        descripcion: Optional[str],
        correlativas: Optional[List[str]] = None,
    ) -> Materia:
        materia = self.obtenerMateria(materia_id)
        materia.nombre = nombre
        materia.codigo = codigo
        materia.descripcion = descripcion or ""
        materia.correlativas = [value for value in (correlativas or []) if value]
        self.broker.actualizarObjeto(materia)
        return materia

    def eliminarMateria(self, materia_id: str) -> None:
        if not self.broker.obtenerPorId("Materia", materia_id):
            raise ValueError("Materia no encontrada")
        self.broker.eliminarObjeto("Materia", materia_id)

    def registrarAlumno(self, nombre: str, email: str, password: str) -> Alumno:
        alumno = Alumno(
            id=None,
            nombre=nombre,
            email=email,
            password=password,
            rol="alumno",
        )
        self.broker.guardarObjeto(alumno)
        return alumno

    def registrarDocente(self, nombre: str, email: str, password: str) -> Docente:
        docente = Docente(
            id=None,
            nombre=nombre,
            email=email,
            password=password,
            rol="docente",
        )
        self.broker.guardarObjeto(docente)
        return docente

    def crearPlan(self, admin: Administrador, nombre: str, descripcion: str) -> Plan:
        plan = admin.crearPlan(nombre, descripcion)
        self.broker.guardarObjeto(plan)
        return plan

    def asignarMateriasAPlan(self, plan_id: str, materias_ids: List[str]) -> Plan:
        data = self.broker.obtenerPorId("Plan", plan_id)
        if not data:
            raise ValueError("Plan no encontrado")
        plan = Plan.from_dict(data)
        plan.addList(materias_ids)
        self.broker.actualizarObjeto(plan)
        return plan

    def obtenerPlan(self, plan_id: str) -> Plan:
        data = self.broker.obtenerPorId("Plan", plan_id)
        if not data:
            raise ValueError("Plan no encontrado")
        return Plan.from_dict(data)

    def actualizarPlan(self, plan_id: str, nombre: str, descripcion: str) -> Plan:
        plan = self.obtenerPlan(plan_id)
        plan.nombre = nombre
        plan.descripcion = descripcion
        self.broker.actualizarObjeto(plan)
        return plan

    def eliminarPlan(self, plan_id: str) -> None:
        if not self.broker.obtenerPorId("Plan", plan_id):
            raise ValueError("Plan no encontrado")
        self.broker.eliminarObjeto("Plan", plan_id)

    def obtenerMateriasDePlan(self, plan_id: str) -> List[Materia]:
        plan = self.obtenerPlan(plan_id)
        materias_dict = {materia.id: materia for materia in self.listarMaterias()}
        return [
            materias_dict[materia_id]
            for materia_id in plan.materias
            if materia_id in materias_dict
        ]

    def crearCohorte(
        self,
        admin: Administrador,
        nombre: str,
        plan_id: str,
        alumnos_ids: Optional[List[str]] = None,
    ) -> Cohorte:
        cohorte = admin.crearCohorte(nombre, plan_id, alumnos_ids)
        self.broker.guardarObjeto(cohorte)
        if alumnos_ids:
            self._asignar_plan_y_cohorte_a_alumnos(alumnos_ids, plan_id, cohorte.id)  # type: ignore[arg-type]
        return cohorte

    def _asignar_plan_y_cohorte_a_alumnos(
        self, alumnos_ids: List[str], plan_id: str, cohorte_id: Optional[str]
    ) -> None:
        for alumno_id in alumnos_ids:
            data = self.broker.obtenerPorId("Usuario", alumno_id)
            if not data or data.get("rol") != "alumno":
                continue
            alumno = Alumno.from_dict(data)
            alumno.plan_id = plan_id
            alumno.cohorte_id = cohorte_id
            self.broker.actualizarObjeto(alumno)

    def crearCurso(
        self,
        admin: Administrador,
        nombre: str,
        materia_id: str,
        cohorte_id: Optional[str],
        docente_id: Optional[str],
    ) -> Curso:
        curso = admin.crearCurso(nombre, materia_id, cohorte_id, docente_id)
        self.broker.guardarObjeto(curso)
        return curso

    def asignarDocente(self, curso_id: str, docente_id: str) -> Curso:
        data = self.broker.obtenerPorId("Curso", curso_id)
        if not data:
            raise ValueError("Curso no encontrado")
        curso = Curso.from_dict(data)
        curso.asignarDocente(docente_id)
        self.broker.actualizarObjeto(curso)
        return curso

    def listarMaterias(self) -> List[Materia]:
        return [Materia.from_dict(item) for item in self.broker.listar("Materia")]

    def listarPlanes(self) -> List[Plan]:
        return [Plan.from_dict(item) for item in self.broker.listar("Plan")]

    def listarCohortes(self) -> List[Cohorte]:
        return [Cohorte.from_dict(item) for item in self.broker.listar("Cohorte")]

    def listarCursos(self) -> List[Curso]:
        return [Curso.from_dict(item) for item in self.broker.listar("Curso")]

    def crearExamen(
        self,
        nombre: str,
        materia_id: str,
        fecha: str,
        curso_id: Optional[str] = None,
        correlativas: Optional[List[str]] = None,
    ) -> Examen:
        correlativas_limpias = [value for value in (correlativas or []) if value]
        examen = Examen(
            id=None,
            nombre=nombre,
            materia_id=materia_id,
            fecha=fecha,
            curso_id=curso_id or None,
            correlativas=correlativas_limpias,
        )
        self.broker.guardarObjeto(examen)
        return examen

    def listarExamenes(self) -> List[Examen]:
        return [Examen.from_dict(item) for item in self.broker.listar("Examen")]

    def listarDocentes(self) -> List[Docente]:
        usuarios = self.broker.listar("Usuario")
        docentes = [
            item for item in usuarios if item.get("rol") == "docente"
        ]
        return [Docente.from_dict(item) for item in docentes]  # type: ignore[arg-type]

    def listarAlumnos(self) -> List[Alumno]:
        usuarios = self.broker.listar("Usuario")
        alumnos = [
            item for item in usuarios if item.get("rol") == "alumno"
        ]
        return [Alumno.from_dict(item) for item in alumnos]  # type: ignore[arg-type]

    def obtenerCohorte(self, cohorte_id: str) -> Cohorte:
        data = self.broker.obtenerPorId("Cohorte", cohorte_id)
        if not data:
            raise ValueError("Cohorte no encontrada")
        return Cohorte.from_dict(data)

    def obtenerDatosCohorte(self, cohorte_id: str) -> tuple[Cohorte, Optional[Plan], List[Alumno]]:
        cohorte = self.obtenerCohorte(cohorte_id)
        plan = None
        if cohorte.plan_id:
            plan_data = self.broker.obtenerPorId("Plan", cohorte.plan_id)
            plan = Plan.from_dict(plan_data) if plan_data else None
        alumnos_map = {alumno.id: alumno for alumno in self.listarAlumnos()}
        cohorte_alumnos = [
            alumnos_map[alumno_id]
            for alumno_id in cohorte.alumnos
            if alumno_id in alumnos_map
        ]
        return cohorte, plan, cohorte_alumnos
