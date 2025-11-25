from app.models.USRs import Administrador
from app.models.materia import Materia
from app.models.plan import Plan

# Nota: cada test recibe el fixture `isolated_broker`, que crea un DBBroker sobre
# un directorio temporal (ver conftest.py). Así, los objetos guardados no tocan
# datos reales y cada prueba empieza limpia.


def test_guardar_y_listar_usa_alias_usuario(isolated_broker):
    # Guarda un administrador y valida que quede accesible como Usuario y como Administrador.
    admin = Administrador(
        id=None,
        nombre="Admin Test",
        email="admin@test.com",
        password="secret",
        rol="administrador",
    )

    stored = isolated_broker.guardarObjeto(admin)

    assert stored["id"] == admin.id
    assert stored["email"] == "admin@test.com"

    usuarios = isolated_broker.listar("Usuario")
    assert any(usuario["email"] == "admin@test.com" for usuario in usuarios)
    assert len(usuarios) == len(isolated_broker.listar("Administrador"))


def test_actualizar_eliminar_y_add_list(isolated_broker):
    # Actualiza una materia, agrega sus IDs a un plan sin duplicados y luego confirma su eliminación.
    materia = Materia(
        id=None,
        nombre="Algebra",
        codigo="ALG-1",
        descripcion="Primer curso",
    )
    stored_materia = isolated_broker.guardarObjeto(materia)

    materia.descripcion = "Curso actualizado"
    updated = isolated_broker.actualizarObjeto(materia)

    assert updated["descripcion"] == "Curso actualizado"

    plan = Plan(
        id=None,
        nombre="Plan 2024",
        descripcion="Plan inicial",
    )
    stored_plan = isolated_broker.guardarObjeto(plan)

    result = isolated_broker.addList(
        "Plan",
        stored_plan["id"],
        "materias",
        [stored_materia["id"], stored_materia["id"], "otra-materia"],
    )

    assert result["materias"] == [stored_materia["id"], "otra-materia"]

    isolated_broker.eliminarObjeto("Materia", stored_materia["id"])

    assert isolated_broker.obtenerPorId("Materia", stored_materia["id"]) is None
