from django.db import transaction
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from academics.models import MateriaAprobada, Inscripcion, Comision


@transaction.atomic
def inscribir_estudiante(estudiante_carrera, comision_id):
    """
    Inscribe a un estudiante en una comisi?n aplicando
    todas las reglas acad?micas.
    """

    # Bloqueamos la comisi?n para evitar condiciones de carrera al actualizar el cupo
    comision = (
        Comision.objects
        .select_for_update()
        .select_related('carrera_materia__carrera', 'carrera_materia__materia', 'cuatrimestre')
        .get(id=comision_id)
    )

    # Carrera activa
    if not estudiante_carrera.activa:
        raise ValidationError(
            "El estudiante no tiene una carrera activa."
        )

    # Comisi?n activa
    if not comision.activa:
        raise ValidationError(
            "La comisi?n no est? activa."
        )

    # La comisi?n pertenece a la carrera del estudiante
    if comision.carrera_materia.carrera != estudiante_carrera.carrera:
        raise ValidationError(
            "La comisi?n no pertenece a la carrera del estudiante."
        )

    # Cupo disponible
    if not comision.tiene_cupo():
        raise ValidationError(
            "La comisi?n no tiene cupo disponible."
        )

    # No puede estar inscripto dos veces a la misma comisi?n
    if Inscripcion.objects.filter(
        estudiante_carrera=estudiante_carrera,
        comision=comision,
        activa=True,
    ).exists():
        raise ValidationError(
            "El estudiante ya est? inscripto en esta comisi?n."
        )

    # No puede estar inscripto a otra comisi?n de la misma materia en el mismo cuatrimestre
    existe = Inscripcion.objects.filter(
        estudiante_carrera=estudiante_carrera,
        comision__cuatrimestre=comision.cuatrimestre,
        comision__carrera_materia__materia=comision.carrera_materia.materia,
        activa=True
    ).exists()
    if existe:
        raise ValidationError(
            "El estudiante ya est? inscripto a esta materia en el cuatrimestre."
        )

    # Validar correlativas aprobadas
    validar_correlativas(estudiante_carrera, comision.carrera_materia)

    try:
        inscripcion = Inscripcion.objects.create(
            estudiante_carrera=estudiante_carrera,
            comision=comision,
            activa=True
        )
        comision.capacidad_actual += 1
        comision.save(update_fields=['capacidad_actual'])
    except IntegrityError as e:
        msg = str(e).lower()
        if 'unique' in msg or 'duplicate' in msg or 'estudiante' in msg:
            raise ValidationError("El estudiante ya est? inscripto en esta comisi?n.") from e
        if 'capacidad' in msg or 'check' in msg:
            raise ValidationError("La comisi?n no tiene cupo disponible.") from e
        raise ValidationError(
            "No se pudo completar la inscripci?n. Verifique que haya cupo y que no est? inscripto."
        ) from e
    return inscripcion


def estudiante_aprobo_materia(estudiante_carrera, materia):
    return MateriaAprobada.objects.filter(
        estudiante_carrera=estudiante_carrera,
        materia=materia
    ).exists()


def validar_correlativas(estudiante_carrera, carrera_materia):
    """
    Valida que el estudiante haya aprobado
    todas las correlativas requeridas.
    """
    # No puede inscribirse a una materia ya aprobada
    if estudiante_aprobo_materia(
        estudiante_carrera,
        carrera_materia.materia
    ):
        raise ValidationError(
            "El estudiante ya tiene aprobada esta materia."
        )

    correlativas = carrera_materia.correlativas.all()

    faltantes = [
        corr.materia.nombre
        for corr in correlativas
        if not estudiante_aprobo_materia(
            estudiante_carrera,
            corr.materia
        )
    ]

    if faltantes:
        raise ValidationError(
            f"No cumple correlativas: {', '.join(faltantes)}"
        )