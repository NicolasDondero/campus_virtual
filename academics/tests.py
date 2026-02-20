from datetime import date

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from academics.services import inscribir_estudiante
from academics.models import (
    Instituto,
    Estudiante,
    EstudianteCarrera,
    Carrera,
    Materia,
    CarreraMateria,
    Comision,
    Cuatrimestre,
    MateriaAprobada,
    Inscripcion
)

User = get_user_model()


class InscripcionServiceTest(TestCase):

    def setUp(self):
        self.instituto = Instituto.objects.create(
            nombre="Instituto de Sistemas",
            codigo="IS"
        )
        self.carrera = Carrera.objects.create(
            instituto=self.instituto,
            nombre="Sistemas",
            codigo="SIS"
        )

        self.user = User.objects.create_user(
            username="estudiante1",
            email="est@test.com",
            password="testpass123"
        )
        self.estudiante_academico = Estudiante.objects.create(
            user=self.user,
            legajo="12345",
            fecha_ingreso=date(2024, 1, 1)
        )
        self.estudiante = EstudianteCarrera.objects.create(
            estudiante=self.estudiante_academico,
            carrera=self.carrera,
            activa=True,
            fecha_inicio=date(2024, 1, 1)
        )

        self.materia = Materia.objects.create(
            nombre="Programación I",
            codigo="PROG1"
        )

        self.carrera_materia = CarreraMateria.objects.create(
            carrera=self.carrera,
            materia=self.materia,
            año=1
        )

        self.cuatrimestre = Cuatrimestre.objects.create(
            nombre="1C",
            año=2026,
            fecha_inicio=date(2026, 3, 1),
            fecha_fin=date(2026, 7, 15)
        )

        self.comision = Comision.objects.create(
            carrera_materia=self.carrera_materia,
            cuatrimestre=self.cuatrimestre,
            nombre="A",
            activa=True,
            capacidad_maxima=30,
            capacidad_actual=0
        )


    def test_inscripcion_exitosa(self):
        inscripcion = inscribir_estudiante(
            self.estudiante,
            self.comision.id,
        )

        self.assertEqual(Inscripcion.objects.count(), 1)
        self.assertEqual(inscripcion.estudiante_carrera, self.estudiante)
        self.assertEqual(self.comision.capacidad_actual, 1)


    def test_falla_si_carrera_inactiva(self):
        self.estudiante.activa = False
        self.estudiante.save()

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision.id)

        self.assertEqual(Inscripcion.objects.count(), 0)


    def test_falla_si_comision_inactiva(self):
        self.comision.activa = False
        self.comision.save()

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision.id)


    def test_falla_si_no_hay_cupo(self):
        self.comision.capacidad_actual = 30
        self.comision.save()

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision.id)


    def test_falla_si_ya_esta_inscripto(self):
        Inscripcion.objects.create(
            estudiante_carrera=self.estudiante,
            comision=self.comision,
            activa=True
        )

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision.id)


    def test_falla_si_no_cumple_correlativas(self):
        materia_prev = Materia.objects.create(nombre="Algoritmos", codigo="ALG")

        carrera_materia_prev = CarreraMateria.objects.create(
            carrera=self.carrera,
            materia=materia_prev,
            año=1
        )

        # agregar correlativa
        self.carrera_materia.correlativas.add(carrera_materia_prev)

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision)

        self.assertEqual(Inscripcion.objects.count(), 0)


    def test_inscribe_si_cumple_correlativas(self):
        materia_prev = Materia.objects.create(nombre="Algoritmos", codigo="ALG")

        carrera_materia_prev = CarreraMateria.objects.create(
            carrera=self.carrera,
            materia=materia_prev,
            año=1
        )

        self.carrera_materia.correlativas.add(carrera_materia_prev)

        MateriaAprobada.objects.create(
            estudiante_carrera=self.estudiante,
            materia=materia_prev,
            fecha_aprobacion=date(2025, 12, 1),
            nota=8
        )

        inscribir_estudiante(self.estudiante, self.comision.id)

        self.assertEqual(Inscripcion.objects.count(), 1)

    def test_rollback_si_falla(self):
        self.estudiante.activa = False
        self.estudiante.save()

        capacidad_inicial = self.comision.capacidad_actual

        with self.assertRaises(ValidationError):
            inscribir_estudiante(self.estudiante, self.comision.id)

        self.comision.refresh_from_db()

        self.assertEqual(self.comision.capacidad_actual, capacidad_inicial)
        self.assertEqual(Inscripcion.objects.count(), 0)