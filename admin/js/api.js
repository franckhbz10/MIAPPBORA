// ==========================================
// CLIENTE API
// ==========================================

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.token = localStorage.getItem('admin_token');
    }

    // Obtener headers con autenticación
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // GET request
    async get(endpoint, params = {}) {
        try {
            const url = new URL(this.baseUrl + endpoint);
            Object.keys(params).forEach(key => {
                if (params[key] !== null && params[key] !== undefined) {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: this.getHeaders()
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('GET Error:', error);
            throw error;
        }
    }

    // POST request
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('POST Error:', error);
            throw error;
        }
    }

    // PUT request
    async put(endpoint, data = {}) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('PUT Error:', error);
            throw error;
        }
    }

    // DELETE request
    async delete(endpoint) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'DELETE',
                headers: this.getHeaders()
            });

            return await this.handleResponse(response);
        } catch (error) {
            console.error('DELETE Error:', error);
            throw error;
        }
    }

    // Manejar respuesta
    async handleResponse(response) {
        const data = await response.json();

        if (!response.ok) {
            // Si es 401, redirigir a login
            if (response.status === 401) {
                this.handleUnauthorized();
            }
            
            throw new Error(data.detail || 'Error en la solicitud');
        }

        return data;
    }

    // Manejar no autorizado
    handleUnauthorized() {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        window.location.href = 'login.html';
    }

    // Establecer token
    setToken(token) {
        this.token = token;
        localStorage.setItem('admin_token', token);
    }

    // Limpiar token
    clearToken() {
        this.token = null;
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
    }
}
