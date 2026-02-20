from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Usuario del sistema con roles"""
    class Roles(models.TextChoices):
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante'
        PROFESOR = 'PROFESOR', 'Profesor'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.ESTUDIANTE,
        db_index=True
    )
    email = models.EmailField(unique=True, db_index=True)
    
    # Auditoría
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['rol', 'is_active']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class StudentProfile(models.Model):
    """Perfil extendido de estudiante"""
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    legajo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9]+$',
            message='El legajo solo puede contener letras mayúsculas y números'
        )]
    )
    fecha_inscripcion = models.DateField(auto_now_add=True, db_index=True)
    carrera = models.ForeignKey(
        'academics.Carrera',
        on_delete=models.CASCADE,
        related_name="perfiles_estudiante",
        null=True,          
        blank=True
    )


    activo = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['legajo']
        verbose_name = 'Perfil de Estudiante'
        verbose_name_plural = 'Perfiles de Estudiantes'
        indexes = [
            models.Index(fields=['legajo', 'activo']),
            models.Index(fields=['carrera', 'activo']),
            models.Index(fields=['fecha_inscripcion']),
        ]

    def __str__(self):
        return f"{self.legajo} - {self.usuario.get_full_name() or self.usuario.username}"


class TeacherProfile(models.Model):
    """Perfil extendido de profesor"""
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    titulo_profesional = models.CharField(max_length=100)
    legajo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        null=True,
        blank=True
    )
    fecha_ingreso = models.DateField(auto_now_add=True, db_index=True)
    activo = models.BooleanField(default=True, db_index=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['usuario__last_name', 'usuario__first_name']
        verbose_name = 'Perfil de Profesor'
        verbose_name_plural = 'Perfiles de Profesores'
        indexes = [
            models.Index(fields=['legajo', 'activo']),
            models.Index(fields=['fecha_ingreso']),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.titulo_profesional}"
