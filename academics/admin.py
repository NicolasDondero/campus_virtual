from django.contrib import admin
from academics.models import (
    Instituto, Cuatrimestre, Carrera, Materia, CarreraMateria, 
    Comision, Inscripcion, Estudiante, EstudianteCarrera, 
    MateriaAprobada, Profesor, Horario, Calificacion
)

class CarreraMateriaInline(admin.TabularInline):
    model = CarreraMateria
    extra = 0
    autocomplete_fields = ('materia',)
    show_change_link = True

@admin.register(CarreraMateria)
class CarreraMateriaAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'materia', 'año', 'cuatrimestre', 'es_obligatoria')
    list_filter = ('carrera', 'es_obligatoria')
    search_fields = (
        'carrera__nombre',
        'materia__nombre',
        'materia__codigo',
    )

@admin.register(Instituto)
class InstitutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre')
    ordering = ('codigo',)

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activa')
    list_filter = ('activa',)
    search_fields = ('codigo', 'nombre')
    ordering = ('codigo',)


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'instituto', 'modalidad', 'activo')
    list_filter = ('activo', 'modalidad', 'instituto')
    search_fields = ('codigo', 'nombre')
    ordering = ('codigo',)
    inlines = [CarreraMateriaInline]

@admin.register(Cuatrimestre)
class CuatrimestreAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('año', 'activo')
    ordering = ('-año', '-fecha_inicio')

class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'aula')


@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'get_materia',
        'get_carrera',
        'profesor',
        'cuatrimestre',
        'capacidad_actual',
        'capacidad_maxima',
        'activa',
    )
    list_filter = ('activa', 'cuatrimestre', 'profesor')
    search_fields = (
        'nombre',
        'carrera_materia__materia__nombre',
        'carrera_materia__materia__codigo',
        'profesor__user__first_name',
        'profesor__user__last_name',
    )
    autocomplete_fields = ('carrera_materia', 'profesor')
    ordering = ('cuatrimestre', 'nombre')
    inlines = [HorarioInline]

    def get_materia(self, obj):
        return obj.carrera_materia.materia
    get_materia.short_description = 'Materia'

    def get_carrera(self, obj):
        return obj.carrera_materia.carrera
    get_carrera.short_description = 'Carrera'


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('estudiante_carrera', 'comision', 'fecha_inscripcion', 'activa')
    list_filter = ('activa', 'fecha_inscripcion')
    search_fields = (
        'estudiante_carrera__estudiante__legajo',
        'estudiante_carrera__estudiante__user__first_name',
        'estudiante_carrera__estudiante__user__last_name',
        'comision__carrera_materia__materia__nombre',
    )
    autocomplete_fields = ('estudiante_carrera', 'comision')
    readonly_fields = ('fecha_inscripcion',)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('legajo', 'user', 'activo', 'fecha_ingreso')
    list_filter = ('activo', 'fecha_ingreso')
    search_fields = ('legajo', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    autocomplete_fields = ('user',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(EstudianteCarrera)
class EstudianteCarreraAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'carrera', 'activa', 'fecha_inicio', 'fecha_fin')
    list_filter = ('activa', 'carrera', 'fecha_inicio')
    search_fields = (
        'estudiante__legajo',
        'estudiante__user__first_name',
        'estudiante__user__last_name',
        'carrera__nombre',
        'carrera__codigo',
    )
    autocomplete_fields = ('estudiante', 'carrera')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(MateriaAprobada)
class MateriaAprobadaAdmin(admin.ModelAdmin):
    list_display = ('estudiante_carrera', 'materia', 'nota', 'condicion', 'fecha_aprobacion')
    list_filter = ('condicion', 'fecha_aprobacion', 'materia')
    search_fields = (
        'estudiante_carrera__estudiante__legajo',
        'materia__nombre',
        'materia__codigo',
    )
    autocomplete_fields = ('estudiante_carrera', 'materia')


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('legajo', 'user', 'titulo_profesional', 'activo', 'fecha_ingreso')
    list_filter = ('activo', 'fecha_ingreso')
    search_fields = (
        'legajo',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'titulo_profesional',
    )
    autocomplete_fields = ('user',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('comision', 'dia_semana', 'hora_inicio', 'hora_fin', 'aula')
    list_filter = ('dia_semana', 'comision__cuatrimestre')
    search_fields = ('comision__nombre', 'aula')
    autocomplete_fields = ('comision',)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'tipo', 'nota', 'fecha')
    list_filter = ('tipo', 'fecha', 'inscripcion__comision__carrera_materia__materia')
    search_fields = (
        'inscripcion__estudiante_carrera__estudiante__legajo',
        'inscripcion__comision__carrera_materia__materia__nombre',
    )
    autocomplete_fields = ('inscripcion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
