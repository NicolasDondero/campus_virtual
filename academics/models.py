from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Instituto(models.Model):
    """Instituto o Facultad de la universidad"""
    nombre = models.CharField(max_length=100, db_index=True)
    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Instituto'
        verbose_name_plural = 'Institutos'
        indexes = [
            models.Index(fields=['codigo', 'activo']),
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Cuatrimestre(models.Model):
    """Período académico (cuatrimestre/semestre)"""
    nombre = models.CharField(max_length=50, db_index=True)
    año = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(db_index=True)
    activo = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-año', '-fecha_inicio']
        verbose_name = 'Cuatrimestre'
        verbose_name_plural = 'Cuatrimestres'
        unique_together = [['nombre', 'año']]
        indexes = [
            models.Index(fields=['año', 'activo']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]

    def __str__(self):
        return f"{self.nombre} {self.año}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio')


class Carrera(models.Model):
    """Carrera universitaria"""
    class Modalidad(models.TextChoices):
        PRESENCIAL = 'PRESENCIAL', 'Presencial'
        VIRTUAL = 'VIRTUAL', 'Virtual'
        MIXTA = 'MIXTA', 'Mixta'

    instituto = models.ForeignKey(
        Instituto,
        on_delete=models.PROTECT,
        related_name='carreras',
        db_index=True
    )
    nombre = models.CharField(max_length=100, db_index=True)
    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    duracion_anios = models.PositiveIntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(10)])
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices, default=Modalidad.PRESENCIAL)
    # MODALIDAD NO LLEVA PAMFLIN
    activo = models.BooleanField(default=True, db_index=True)
    materias = models.ManyToManyField('Materia', through='CarreraMateria', related_name='carreras')
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        indexes = [
            models.Index(fields=['codigo', 'activo']),
            models.Index(fields=['instituto', 'activo']),
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Materia(models.Model):
    """Materia/Asignatura universitaria"""
    nombre = models.CharField(max_length=100, db_index=True)
    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    creditos = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(20)])
    horas_catedra = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        indexes = [
            models.Index(fields=['codigo', 'activa']),
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class CarreraMateria(models.Model):
    """Relación entre Carrera y Materia con información adicional"""
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.CASCADE,
        related_name='carrera_materias',
        db_index=True,
        null=True,          
        blank=True
    )
    materia = models.ForeignKey(
        Materia,
        on_delete=models.PROTECT,
        related_name='carrera_materias',
        db_index=True
    )
    año = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        db_index=True
    )
    cuatrimestre = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        null=True,
        blank=True
    )
    es_obligatoria = models.BooleanField(default=True, db_index=True)
    correlativas = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='es_correlativa_de',
        help_text='Materias de la misma carrera que deben aprobarse antes'
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['carrera', 'año', 'cuatrimestre']
        verbose_name = 'Materia de Carrera'
        verbose_name_plural = 'Materias de Carreras'
        unique_together = [['carrera', 'materia']]
        indexes = [
            models.Index(fields=['carrera', 'año', 'es_obligatoria']),
            models.Index(fields=['materia']),
        ]

    def __str__(self):
        return f"{self.carrera.codigo} - {self.materia.codigo} (Año {self.año})"

    def clean(self):
        """Valida que las correlativas pertenezcan a la misma carrera"""
        from django.core.exceptions import ValidationError
        if self.pk:  # Solo validar si ya existe (para poder acceder a correlativas)
            correlativas = self.correlativas.all()
            for corr in correlativas:
                if corr.carrera != self.carrera:
                    raise ValidationError(
                        f'La correlativa {corr.materia} pertenece a otra carrera ({corr.carrera}). '
                        f'Las correlativas deben ser de la misma carrera ({self.carrera}).'
                    )


class Comision(models.Model):
    """Comisión/Grupo de una materia en un cuatrimestre"""
    carrera_materia = models.ForeignKey(
        CarreraMateria,
        on_delete=models.PROTECT,
        related_name='comisiones',
        db_index=True
    )
    cuatrimestre = models.ForeignKey(
        Cuatrimestre,
        on_delete=models.PROTECT,
        related_name='comisiones',
        db_index=True
    )
    nombre = models.CharField(max_length=50, db_index=True)
    capacidad_maxima = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    capacidad_actual = models.PositiveIntegerField(default=0)
    profesor = models.ForeignKey(
        'Profesor',
        on_delete=models.PROTECT,
        related_name='comisiones',
        null=True,
        blank=True,
        db_index=True,
        help_text="Profesor a cargo de la comisión"
    )
    activa = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cuatrimestre', 'carrera_materia', 'nombre']
        verbose_name = 'Comisión'
        verbose_name_plural = 'Comisiones'
        unique_together = [['carrera_materia', 'cuatrimestre', 'nombre']]
        indexes = [
            models.Index(fields=['carrera_materia', 'cuatrimestre', 'activa']),
            models.Index(fields=['capacidad_actual']),
        ]

    def __str__(self):
        return (
            f"{self.carrera_materia.materia.codigo} - "
            f"{self.nombre} ({self.cuatrimestre})"
        )


    def clean(self):
        from django.core.exceptions import ValidationError

        if self.capacidad_actual > self.capacidad_maxima:
            raise ValidationError('La capacidad actual no puede ser mayor a la máxima')

        if not self.carrera_materia.materia.activa:
            raise ValidationError('La materia no está activa')

        if not self.carrera_materia.carrera.activo:
            raise ValidationError('La carrera no está activa')

    def tiene_cupo(self):
        return self.capacidad_actual < self.capacidad_maxima


class Horario(models.Model):
    """Horario de cursada de una comisión"""
    class DiaSemana(models.IntegerChoices):
        LUNES = 1, 'Lunes'
        MARTES = 2, 'Martes'
        MIERCOLES = 3, 'Miércoles'
        JUEVES = 4, 'Jueves'
        VIERNES = 5, 'Viernes'
        SABADO = 6, 'Sábado'
        DOMINGO = 7, 'Domingo'

    comision = models.ForeignKey(
        Comision,
        on_delete=models.CASCADE,
        related_name='horarios',
        db_index=True
    )
    dia_semana = models.IntegerField(choices=DiaSemana.choices, db_index=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    aula = models.CharField(max_length=50, blank=True, help_text="Aula o espacio de cursada")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['comision', 'dia_semana', 'hora_inicio']
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        indexes = [
            models.Index(fields=['comision', 'dia_semana']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.hora_fin <= self.hora_inicio:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio')

    def __str__(self):
        return f"{self.comision} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"


class Inscripcion(models.Model):
    """
    Inscripción de un estudiante (en una carrera) a una comisión
    """

    estudiante_carrera = models.ForeignKey(
        'EstudianteCarrera',
        on_delete=models.PROTECT,
        related_name='inscripciones',
        db_index=True
    )

    comision = models.ForeignKey(
        'Comision',
        on_delete=models.PROTECT,
        related_name='inscripciones',
        db_index=True,
    )

    # Denormalizamos para poder definir constraints fuertes por materia/cuatrimestre
    materia = models.ForeignKey(
        'Materia',
        on_delete=models.PROTECT,
        related_name='inscripciones',
        db_index=True,
        null=True,
        blank=True,
    )
    cuatrimestre = models.ForeignKey(
        'Cuatrimestre',
        on_delete=models.PROTECT,
        related_name='inscripciones',
        db_index=True,
        null=True,
        blank=True,
    )

    activa = models.BooleanField(default=True, db_index=True)

    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        indexes = [
            models.Index(fields=['estudiante_carrera', 'activa']),
            models.Index(fields=['comision', 'activa']),
            models.Index(fields=['materia', 'cuatrimestre', 'activa']),
        ]
        # 1) No permitir dos inscripciones a la misma comisión
        # 2) No permitir más de una inscripción ACTIVA por materia/cuatrimestre
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante_carrera', 'comision'],
                name='unique_inscripcion_estudiante_comision',
            ),
            models.UniqueConstraint(
                fields=['estudiante_carrera', 'materia', 'cuatrimestre'],
                condition=Q(activa=True),
                name='unique_inscripcion_activa_por_materia_cuatrimestre',
            ),
        ]

    def __str__(self):
        return (
            f"{self.estudiante_carrera.estudiante.legajo} → "
            f"{self.comision}"
        )

    def clean(self):
        """
        Validaciones de integridad básicas (no reglas de negocio complejas)
        """
        if self.estudiante_carrera and self.comision:
            # Sincronizamos materia y cuatrimestre desde la comisión por si no vinieron seteados
            self.materia = self.comision.carrera_materia.materia
            self.cuatrimestre = self.comision.cuatrimestre

            # 1) misma comisión
            qs = Inscripcion.objects.filter(
                estudiante_carrera=self.estudiante_carrera,
                comision=self.comision,
                activa=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Este estudiante ya está inscripto en esta comisión."
                )

            # 2) otra comisión de la misma materia en el mismo cuatrimestre
            qs_materia = Inscripcion.objects.filter(
                estudiante_carrera=self.estudiante_carrera,
                materia=self.materia,
                cuatrimestre=self.cuatrimestre,
                activa=True,
            )
            if self.pk:
                qs_materia = qs_materia.exclude(pk=self.pk)
            if qs_materia.exists():
                raise ValidationError(
                    "Este estudiante ya tiene una inscripción activa en esta materia y cuatrimestre."
                )
        if not self.estudiante_carrera.activa:
            raise ValidationError(
                "El estudiante no tiene una carrera activa."
            )

        if not self.comision.activa:
            raise ValidationError(
                "La comisión no está activa."
            )

    def dar_baja(self):
        """Da de baja una inscripción"""
        if self.activa:
            self.activa = False
            self.fecha_baja = timezone.now()
            self.save(update_fields=['activa', 'fecha_baja'])
            # Decrementar capacidad de la comisión
            self.comision.capacidad_actual = max(0, self.comision.capacidad_actual - 1)
            self.comision.save(update_fields=['capacidad_actual'])


class Estudiante(models.Model):
    """
    Representa a un estudiante desde el punto de vista académico.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='estudiante'
    )

    legajo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    activo = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Estado académico del estudiante"
    )

    fecha_ingreso = models.DateField()
    fecha_egreso = models.DateField(null=True, blank=True)

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['legajo']
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        indexes = [
            models.Index(fields=['legajo', 'activo']),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.user.get_full_name() or self.user.username}"

    def get_carrera_activa(self):
        """Retorna la carrera activa del estudiante"""
        return self.carreras.filter(activa=True).first()

    def materias_aprobadas_count(self):
        """Retorna la cantidad de materias aprobadas"""
        carrera_activa = self.get_carrera_activa()
        if carrera_activa:
            return carrera_activa.materias_aprobadas.count()
        return 0


class Profesor(models.Model):
    """
    Representa a un profesor desde el punto de vista académico.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='profesor'
    )

    legajo = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    titulo_profesional = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Estado del profesor"
    )

    fecha_ingreso = models.DateField()
    fecha_egreso = models.DateField(null=True, blank=True)

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'
        indexes = [
            models.Index(fields=['legajo', 'activo']),
        ]

    def __str__(self):
        return f"{self.legajo or 'Sin legajo'} - {self.user.get_full_name() or self.user.username}"

    def comisiones_activas(self):
        """Retorna las comisiones activas del profesor"""
        return self.comisiones.filter(activa=True)


from django.db import models
from django.core.exceptions import ValidationError


class EstudianteCarrera(models.Model):
    """
    Relación entre un Estudiante y una Carrera.
    Mantiene historial académico.
    """

    estudiante = models.ForeignKey(
        'Estudiante',
        on_delete=models.PROTECT,
        related_name='carreras',
        db_index=True
    )

    carrera = models.ForeignKey(
        'Carrera',
        on_delete=models.PROTECT,
        related_name='estudiantes',
        db_index=True
    )

    activa = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indica si es la carrera activa del estudiante"
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carrera del Estudiante'
        verbose_name_plural = 'Carreras de Estudiantes'
        indexes = [
            models.Index(fields=['estudiante', 'activa']),
            models.Index(fields=['carrera', 'activa']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante', 'carrera'],
                name='unique_estudiante_carrera'
            )
        ]

    def __str__(self):
        estado = "Activa" if self.activa else "Histórica"
        return f"{self.estudiante.legajo} - {self.carrera.codigo} ({estado})"

    def clean(self):
        """
        Regla: un estudiante solo puede tener UNA carrera activa.
        """
        if self.activa:
            existe = EstudianteCarrera.objects.filter(
                estudiante=self.estudiante,
                activa=True
            ).exclude(pk=self.pk).exists()

            if existe:
                raise ValidationError(
                    "El estudiante ya tiene una carrera activa."
                )


class MateriaAprobada(models.Model):
    """
    Registro de una materia aprobada por un estudiante en una carrera
    """
    class Condicion(models.TextChoices):
        REGULAR = 'REGULAR', 'Regular'
        PROMOCIONADO = 'PROMOCIONADO', 'Promocionado'
        EQUIVALENCIA = 'EQUIVALENCIA', 'Equivalencia'

    estudiante_carrera = models.ForeignKey(
        'EstudianteCarrera',
        on_delete=models.PROTECT,
        related_name='materias_aprobadas',
        db_index=True
    )

    materia = models.ForeignKey(
        'Materia',
        on_delete=models.PROTECT,
        related_name='aprobaciones',
        db_index=True
    )

    fecha_aprobacion = models.DateField()
    nota = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Nota final (escala 1-10)"
    )
    condicion = models.CharField(
        max_length=20,
        choices=Condicion.choices,
        default=Condicion.REGULAR,
        db_index=True
    )
    acta_numero = models.CharField(max_length=50, blank=True, help_text="Número de acta de examen")

    class Meta:
        verbose_name = 'Materia aprobada'
        verbose_name_plural = 'Materias aprobadas'
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante_carrera', 'materia'],
                name='unique_materia_aprobada_por_estudiante'
            )
        ]
        indexes = [
            models.Index(fields=['estudiante_carrera', 'materia']),
            models.Index(fields=['fecha_aprobacion']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.nota < 1 or self.nota > 10:
            raise ValidationError('La nota debe estar entre 1 y 10')

    def __str__(self):
        return f"{self.materia} aprobada por {self.estudiante_carrera} - Nota: {self.nota}"


class Calificacion(models.Model):
    """
    Calificaciones parciales y finales de un estudiante en una inscripción
    """
    class TipoEvaluacion(models.TextChoices):
        PARCIAL_1 = 'PARCIAL_1', 'Parcial 1'
        PARCIAL_2 = 'PARCIAL_2', 'Parcial 2'
        RECUPERATORIO = 'RECUPERATORIO', 'Recuperatorio'
        FINAL = 'FINAL', 'Examen Final'
        TRABAJO_PRACTICO = 'TP', 'Trabajo Práctico'
        OTRO = 'OTRO', 'Otro'

    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        db_index=True
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoEvaluacion.choices,
        db_index=True
    )
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Nota (escala 0-10)"
    )
    fecha = models.DateField(db_index=True)
    observaciones = models.TextField(blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['inscripcion', 'fecha']
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        indexes = [
            models.Index(fields=['inscripcion', 'tipo']),
            models.Index(fields=['fecha']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.nota < 0 or self.nota > 10:
            raise ValidationError('La nota debe estar entre 0 y 10')

    def __str__(self):
        return f"{self.inscripcion} - {self.get_tipo_display()}: {self.nota}"
