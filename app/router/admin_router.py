"""Endpoints de administrador que cubren los CU-002 al CU-007."""

from __future__ import annotations

from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.controllers.administrador_service import AdministradorService
from app.utils.auth import get_current_user
from app.utils.navigation import menu_for_role

router = APIRouter(prefix="/admin", tags=["Administrador"])
service = AdministradorService()


def _require_admin(request: Request):
    usuario = get_current_user(request)
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido")
    return usuario


@router.get("/registrar_usuario", response_class=HTMLResponse)
async def registrar_usuario_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "admin/registrar_usuario.html",
        {
            "request": request,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Registrar usuarios",
        },
    )


@router.post("/registrar_usuario")
async def registrar_usuario_action(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    tipo: str = Form(...),
) -> RedirectResponse:
    _require_admin(request)
    if tipo == "alumno":
        service.registrarAlumno(nombre, email, password)
    elif tipo == "docente":
        service.registrarDocente(nombre, email, password)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo invalido")
    return RedirectResponse(
        request.url_for("dashboard"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/crear_materia", response_class=HTMLResponse)
async def crear_materia_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    materias = service.listarMaterias()
    return templates.TemplateResponse(
        "admin/crear_materia.html",
        {
            "request": request,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Crear materia",
            "materias": materias,
        },
    )


@router.post("/crear_materia")
async def crear_materia_action(
    request: Request,
    nombre: str = Form(...),
    codigo: str = Form(...),
    descripcion: str = Form(""),
    correlativas: List[str] = Form(default=[]),
) -> RedirectResponse:
    admin = _require_admin(request)
    service.crearMateria(admin, nombre, codigo, descripcion, correlativas or None)
    return RedirectResponse(
        request.url_for("dashboard"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/crear_plan", response_class=HTMLResponse)
async def crear_plan_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    planes = service.listarPlanes()
    materias = service.listarMaterias()
    plan_id = request.query_params.get("plan_id")
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    selected_plan = None
    plan_materias: List = []
    if plan_id:
        try:
            selected_plan = service.obtenerPlan(plan_id)
            plan_materias = service.obtenerMateriasDePlan(plan_id)
        except ValueError:
            error = "Plan no encontrado"
            selected_plan = None
            plan_materias = []
    return templates.TemplateResponse(
        "admin/crear_plan.html",
        {
            "request": request,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Crear plan",
            "planes": planes,
            "materias": materias,
            "selected_plan": selected_plan,
            "plan_materias": plan_materias,
            "success": success,
            "error": error,
        },
    )


@router.post("/crear_plan")
async def crear_plan_action(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
) -> RedirectResponse:
    admin = _require_admin(request)
    service.crearPlan(admin, nombre, descripcion)
    return RedirectResponse(
        request.url_for("dashboard"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/plan/actualizar")
async def actualizar_plan_action(
    request: Request,
    plan_id: str = Form(...),
    nombre: str = Form(...),
    descripcion: str = Form(""),
) -> RedirectResponse:
    _require_admin(request)
    url = request.url_for("crear_plan_view")
    try:
        service.actualizarPlan(plan_id, nombre, descripcion)
    except ValueError:
        return RedirectResponse(
            f"{url}?error={quote('Plan no encontrado')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        f"{url}?plan_id={plan_id}&success={quote('Plan actualizado correctamente')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/plan/eliminar")
async def eliminar_plan_action(
    request: Request,
    plan_id: str = Form(...),
) -> RedirectResponse:
    _require_admin(request)
    url = request.url_for("crear_plan_view")
    try:
        service.eliminarPlan(plan_id)
    except ValueError:
        return RedirectResponse(
            f"{url}?error={quote('Plan no encontrado')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        f"{url}?success={quote('Plan eliminado correctamente')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/asignar_materia_plan", response_class=HTMLResponse)
async def asignar_materia_plan_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    planes = service.listarPlanes()
    materias = service.listarMaterias()
    return templates.TemplateResponse(
        "admin/asignar_materia_plan.html",
        {
            "request": request,
            "planes": planes,
            "materias": materias,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Asignar materias a plan",
        },
    )


@router.post("/asignar_materia_plan")
async def asignar_materia_plan_action(
    request: Request,
    plan_id: str = Form(...),
    materias_ids: List[str] = Form(default=[]),
) -> RedirectResponse:
    _require_admin(request)
    url = request.url_for("crear_plan_view")
    try:
        service.asignarMateriasAPlan(plan_id, materias_ids)
    except ValueError:
        return RedirectResponse(
            f"{url}?error={quote('Plan no encontrado')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        f"{url}?plan_id={plan_id}&success={quote('Materias asignadas correctamente')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/crear_cohorte", response_class=HTMLResponse)
async def crear_cohorte_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    planes = service.listarPlanes()
    alumnos = service.listarAlumnos()
    cohortes = service.listarCohortes()
    cohorte_id = request.query_params.get("cohorte_id")
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    selected_cohorte = None
    cohorte_plan = None
    cohorte_plan_materias: List = []
    cohorte_alumnos: List = []
    if cohorte_id:
        try:
            selected_cohorte, cohorte_plan, cohorte_alumnos = service.obtenerDatosCohorte(cohorte_id)
            if cohorte_plan:
                cohorte_plan_materias = service.obtenerMateriasDePlan(cohorte_plan.id)  # type: ignore[arg-type]
        except ValueError:
            error = "Cohorte no encontrada"
            selected_cohorte = None
            cohorte_plan = None
            cohorte_plan_materias = []
            cohorte_alumnos = []
    return templates.TemplateResponse(
        "admin/crear_cohorte.html",
        {
            "request": request,
            "planes": planes,
            "alumnos": alumnos,
            "cohortes": cohortes,
            "selected_cohorte": selected_cohorte,
            "cohorte_plan": cohorte_plan,
            "cohorte_plan_materias": cohorte_plan_materias,
            "cohorte_alumnos": cohorte_alumnos,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Crear cohorte",
            "success": success,
            "error": error,
        },
    )


@router.post("/crear_cohorte")
async def crear_cohorte_action(
    request: Request,
    nombre: str = Form(...),
    plan_id: str = Form(...),
    alumnos_ids: List[str] = Form(default=[]),
) -> RedirectResponse:
    admin = _require_admin(request)
    service.crearCohorte(admin, nombre, plan_id, alumnos_ids or None)
    return RedirectResponse(
        request.url_for("dashboard"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/crear_curso", response_class=HTMLResponse)
async def crear_curso_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    materias = service.listarMaterias()
    cohortes = service.listarCohortes()
    docentes = service.listarDocentes()
    cursos = service.listarCursos()
    materia_map = {materia.id: materia for materia in materias if materia.id}
    cohorte_map = {cohorte.id: cohorte for cohorte in cohortes if cohorte.id}
    docente_map = {docente.id: docente for docente in docentes if docente.id}
    cursos_detalle = []
    for curso in cursos:
        materia = materia_map.get(curso.materia_id)
        cohorte = cohorte_map.get(curso.cohorte_id)
        docente = docente_map.get(curso.docente_id)
        cursos_detalle.append(
            {
                "id": curso.id,
                "nombre": curso.nombre,
                "materia_nombre": materia.nombre if materia else curso.materia_id,
                "cohorte_nombre": cohorte.nombre if cohorte else "Sin cohorte asignada",
                "docente_nombre": docente.nombre if docente else "Sin docente asignado",
            }
        )
    return templates.TemplateResponse(
        "admin/crear_curso.html",
        {
            "request": request,
            "materias": materias,
            "cohortes": cohortes,
            "docentes": docentes,
            "cursos": cursos_detalle,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Crear curso",
        },
    )


@router.post("/crear_curso")
async def crear_curso_action(
    request: Request,
    nombre: str = Form(...),
    materia_id: str = Form(...),
    cohorte_id: str = Form(None),
    docente_id: str = Form(None),
) -> RedirectResponse:
    admin = _require_admin(request)
    service.crearCurso(
        admin,
        nombre,
        materia_id,
        cohorte_id or None,
        docente_id or None,
    )
    return RedirectResponse(
        request.url_for("dashboard"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/examenes", response_class=HTMLResponse, name="examenes_view")
async def examenes_view(request: Request) -> HTMLResponse:
    admin = _require_admin(request)
    templates = request.app.state.templates
    planes = service.listarPlanes()
    plan_id = request.query_params.get("plan_id") if planes else None
    if plan_id not in {p.id for p in planes if p.id}:
        plan_id = planes[0].id if planes and planes[0].id else None
    materias = service.obtenerMateriasDePlan(plan_id) if plan_id else []
    cursos = [curso for curso in service.listarCursos() if not materias or curso.materia_id in {m.id for m in materias}]
    examenes = service.listarExamenes()
    alumnos = service.listarAlumnos()
    materia_map = {materia.id: materia for materia in materias if materia.id}
    curso_map = {curso.id: curso for curso in cursos if curso.id}
    examenes_detalle = []
    for examen in examenes:
        correlativas = [
            materia_map[correlativa_id].nombre
            for correlativa_id in examen.correlativas
            if correlativa_id in materia_map
        ]
        alumnos_inscriptos = [
            alumno
            for alumno in alumnos
            if examen.id and examen.id in alumno.examenesInscripto
        ]
        examenes_detalle.append(
            {
                "examen": examen,
                "materia_nombre": materia_map.get(examen.materia_id).nombre
                if materia_map.get(examen.materia_id)
                else examen.materia_id,
                "curso_nombre": curso_map.get(examen.curso_id).nombre
                if examen.curso_id and curso_map.get(examen.curso_id)
                else "Sin curso asignado",
                "correlativas": correlativas,
                "alumnos": alumnos_inscriptos,
            }
        )
    success = request.query_params.get("success")
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "admin/examenes.html",
        {
            "request": request,
            "usuario": admin,
            "nav_items": menu_for_role(admin.rol),
            "page_title": "Gestion de examenes",
            "planes": planes,
            "plan_id": plan_id,
            "materias": materias,
            "cursos": cursos,
            "examenes_detalle": examenes_detalle,
            "success": success,
            "error": error,
        },
    )


@router.post("/examenes")
async def crear_examen_action(
    request: Request,
    nombre: str = Form(...),
    fecha: str = Form(...),
    materia_id: str = Form(...),
    curso_id: str = Form(""),
    correlativas: List[str] = Form(default=[]),
    plan_id: str = Form(...),
) -> RedirectResponse:
    _require_admin(request)
    url = request.url_for("examenes_view")
    try:
        if plan_id not in {plan.id for plan in service.listarPlanes() if plan.id}:
            raise ValueError("Plan invalido")
        materias_plan = {m.id for m in service.obtenerMateriasDePlan(plan_id)}
        if materia_id not in materias_plan:
            raise ValueError("La materia no pertenece al plan seleccionado")
        correlativas_limpias = [cid for cid in (correlativas or []) if cid in materias_plan]
        service.crearExamen(
            nombre=nombre,
            materia_id=materia_id,
            fecha=fecha,
            curso_id=curso_id or None,
            correlativas=correlativas_limpias or None,
        )
    except ValueError as exc:
        return RedirectResponse(
            f"{url}?error={quote(str(exc))}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        f"{url}?success={quote('Examen creado correctamente')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
