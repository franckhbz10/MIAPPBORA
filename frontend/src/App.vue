<template>
  <div id="app">
    <Navigation v-if="shouldShowNav" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navigation from './components/Navigation.vue'

export default {
  name: 'App',
  components: {
    Navigation
  },
  setup() {
    const route = useRoute()
    
    // Ocultar navbar en la página de autenticación
    const shouldShowNav = computed(() => {
      return route.path !== '/'
    })
    
    return {
      shouldShowNav
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

@font-face {
  font-family: 'Wonderian';
  src: url('./assets/fonts/Wonderian.otf');
}
body {
  font-family: 'Wonderian', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>