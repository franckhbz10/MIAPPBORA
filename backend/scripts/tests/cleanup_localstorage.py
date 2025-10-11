"""
Script para limpiar datos antiguos del localStorage del navegador
Ejecuta esto en la consola del navegador (F12) para limpiar datos antiguos
"""

# JavaScript para ejecutar en la consola del navegador
javascript_code = """
// Script de limpieza de localStorage para MIAPPBORA
// Copia y pega este código en la consola del navegador (F12)

(function() {
    console.log('🧹 Iniciando limpieza de localStorage...');
    
    // Claves antiguas que ya no se usan (sin asociación al usuario)
    const oldKeys = [
        'gameScore',
        'totalQuestions',
        'correctAnswers',
        'streak'
    ];
    
    let removed = 0;
    
    oldKeys.forEach(key => {
        if (localStorage.getItem(key) !== null) {
            localStorage.removeItem(key);
            console.log(`✅ Eliminado: ${key}`);
            removed++;
        }
    });
    
    if (removed === 0) {
        console.log('✨ No se encontraron datos antiguos para limpiar');
    } else {
        console.log(`✅ Limpieza completada: ${removed} items eliminados`);
    }
    
    console.log('\\n📊 Estado actual del localStorage:');
    console.log('Total de items:', localStorage.length);
    
    // Mostrar datos por usuario
    const gameKeys = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('game_')) {
            gameKeys.push(key);
        }
    }
    
    if (gameKeys.length > 0) {
        console.log('\\n🎮 Datos de juego encontrados:');
        gameKeys.forEach(key => {
            console.log(`  - ${key}: ${localStorage.getItem(key)}`);
        });
    }
    
    // Mostrar usuario actual
    const user = localStorage.getItem('user');
    if (user) {
        const userData = JSON.parse(user);
        console.log('\\n👤 Usuario actual:', userData.username || userData.email);
        console.log('   ID:', userData.id);
    }
    
    console.log('\\n✅ Limpieza completada exitosamente');
})();
"""

print("=" * 80)
print("  SCRIPT DE LIMPIEZA DE LOCALSTORAGE - MIAPPBORA")
print("=" * 80)
print()
print("📋 INSTRUCCIONES:")
print()
print("1. Abre la aplicación en el navegador")
print("2. Presiona F12 para abrir las herramientas de desarrollador")
print("3. Ve a la pestaña 'Console' (Consola)")
print("4. Copia y pega el siguiente código:")
print()
print("-" * 80)
print(javascript_code)
print("-" * 80)
print()
print("5. Presiona Enter para ejecutar")
print()
print("=" * 80)
print("  CAMBIOS REALIZADOS EN EL SISTEMA")
print("=" * 80)
print()
print("✅ Ahora los datos del juego se guardan POR USUARIO:")
print("   - Antes: 'gameScore' → Compartido por todos")
print("   - Ahora: 'game_123_score' → Específico del usuario ID 123")
print()
print("✅ Formato de las claves en localStorage:")
print("   - game_{userId}_score")
print("   - game_{userId}_totalQuestions")
print("   - game_{userId}_correctAnswers")
print("   - game_{userId}_streak")
print()
print("✅ Al cerrar sesión se limpian automáticamente los datos del juego")
print()
print("=" * 80)
