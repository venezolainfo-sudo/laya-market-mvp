# Checklist Google Play — LAYA Market

- Package reservado: `com.laya.market` (cambiar antes del primer release si la marca usa otro dominio).
- Target Android API 36 configurado.
- Generar AAB firmado con EAS Build o Gradle.
- Crear URL pública HTTPS para Política de Privacidad.
- Completar formulario “Seguridad de los datos” según SDKs reales instalados.
- Declarar recopilación/uso de: cuenta, dirección de entrega, datos de compra y datos de pago procesados por terceros según implementación final.
- No solicitar permisos Android no utilizados; actualmente `permissions: []`.
- Configurar eliminación de cuenta/datos antes de lanzamiento si se crean cuentas desde la app.
- Proveer datos de contacto del desarrollador y política de reembolsos/entregas.
- Capturas para teléfonos y, si se distribuye, tablets.
- Icono 512x512, feature graphic, descripción corta/larga.
- Clasificación de contenido.
- Pruebas internas/cerradas antes de producción cuando Play Console lo exija para la cuenta.
- Sustituir credenciales demo y secretos.
- Revisar cumplimiento local de comercio electrónico, privacidad, consumidores y facturación en Argentina/Venezuela antes de producción.
