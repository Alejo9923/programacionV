import requests
from django.shortcuts import render, redirect
from django.contrib import messages

# URL base de la API — todas las vistas web consumen la API REST interna
API_BASE = 'http://127.0.0.1:8000/api'


def get_auth_headers(request):
    """
    Devuelve el header de autorización JWT si el usuario tiene sesión activa.
    Se usa en todas las vistas que consumen endpoints protegidos de la API.
    """
    token = request.session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def login_view(request):
    """
    GET  /web/login/ → muestra el formulario de login
    POST /web/login/ → envía credenciales a la API y guarda el token en sesión
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Llamamos al endpoint de login de nuestra API
        response = requests.post(f'{API_BASE}/auth/login/', json={
            'email': email,
            'password': password
        })

        if response.status_code == 200:
            data = response.json()
            # Guardamos el token en la sesión del navegador
            request.session['access_token'] = data['access']
            request.session['refresh_token'] = data['refresh']
            return redirect('web:catalog')
        else:
            return render(request, 'web/login.html', {'error': 'Credenciales incorrectas'})

    return render(request, 'web/login.html')


def register_view(request):
    """
    GET  /web/register/ → muestra el formulario de registro
    POST /web/register/ → envía datos a la API y redirige al login
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, 'web/register.html', {'error': 'Las contraseñas no coinciden'})

        response = requests.post(f'{API_BASE}/auth/register/', json={
            'username': username,
            'email': email,
            'password': password,
            'password2': password2
        })

        if response.status_code == 201:
            messages.success(request, 'Cuenta creada. Podés iniciar sesión.')
            return redirect('web:login')
        else:
            error = response.json()
            return render(request, 'web/register.html', {'error': error})

    return render(request, 'web/register.html')


def logout_view(request):
    """
    POST /web/logout/ → invalida el token y limpia la sesión
    """
    headers = get_auth_headers(request)
    refresh_token = request.session.get('refresh_token')

    if refresh_token:
        requests.post(f'{API_BASE}/auth/logout/', json={
            'refresh': refresh_token
        }, headers=headers)

    # Limpiamos la sesión local independientemente de la respuesta de la API
    request.session.flush()
    return redirect('web:login')


def catalog_view(request):
    """
    GET /web/products/ → lista pública de productos con filtros
    No requiere autenticación.
    """
    params = {}
    if request.GET.get('search'):
        params['search'] = request.GET.get('search')
    if request.GET.get('categoria'):
        params['categoria'] = request.GET.get('categoria')
    if request.GET.get('precio_min'):
        params['precio_min'] = request.GET.get('precio_min')
    if request.GET.get('precio_max'):
        params['precio_max'] = request.GET.get('precio_max')

    # Obtenemos productos y categorías de la API
    productos_resp = requests.get(f'{API_BASE}/products/', params=params)
    categorias_resp = requests.get(f'{API_BASE}/categories/')

    productos = productos_resp.json() if productos_resp.status_code == 200 else []
    categorias = categorias_resp.json() if categorias_resp.status_code == 200 else []

    return render(request, 'web/catalog.html', {
        'productos': productos,
        'categorias': categorias,
    })


def product_detail_view(request, producto_id):
    """
    GET  /web/products/{id}/ → detalle del producto con variantes
    POST /web/products/{id}/ → agrega variante al carrito
    """
    response = requests.get(f'{API_BASE}/products/{producto_id}/')
    if response.status_code != 200:
        messages.error(request, 'Producto no encontrado.')
        return redirect('web:catalog')

    producto = response.json()

    if request.method == 'POST':
        headers = get_auth_headers(request)
        if not headers:
            return redirect('web:login')

        variante_id = request.POST.get('variante_id')
        
        try:
            cantidad = int(request.POST.get('cantidad', 1))
            if cantidad < 1:
                raise ValueError
        except ValueError:
            return render(request, 'web/product_detail.html', {
                'producto': producto,
                'error': 'La cantidad debe ser un número entero mayor a 0.'
            })

        resp = requests.post(f'{API_BASE}/cart/items/', json={
            'variante_id': int(variante_id),
            'cantidad': int(cantidad)
        }, headers=headers)

        if resp.status_code == 201:
            messages.success(request, 'Producto agregado al carrito.')
            return redirect('web:cart')
        else:
            error = resp.json().get('error', 'Error al agregar al carrito.')
            return render(request, 'web/product_detail.html', {
                'producto': producto,
                'error': error
            })

    return render(request, 'web/product_detail.html', {'producto': producto})


def cart_view(request):
    """
    GET /web/cart/ → muestra el carrito del usuario autenticado
    Redirige al login si no hay sesión activa.
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    response = requests.get(f'{API_BASE}/cart/', headers=headers)
    cart = response.json() if response.status_code == 200 else None

    return render(request, 'web/cart.html', {'cart': cart})


def update_cart_item_view(request, item_id):
    """
    POST /web/cart/items/{id}/update/ → actualiza la cantidad de un item
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        # Primero obtenemos el item actual para saber su variante_id
        cart_resp = requests.get(f'{API_BASE}/cart/', headers=headers)
        cart = cart_resp.json()
        variante_id = None
        for item in cart['items']:
            if item['id'] == item_id:
                variante_id = item['variante']['id']
                break

        requests.put(f'{API_BASE}/cart/items/{item_id}/', json={
            'variante_id': variante_id,
            'cantidad': int(cantidad)
        }, headers=headers)

    return redirect('web:cart')


def remove_cart_item_view(request, item_id):
    """
    POST /web/cart/items/{id}/remove/ → elimina un item del carrito
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        requests.delete(f'{API_BASE}/cart/items/{item_id}/', headers=headers)

    return redirect('web:cart')


def clear_cart_view(request):
    """
    POST /web/cart/clear/ → vacía el carrito completo
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        requests.delete(f'{API_BASE}/cart/clear/', headers=headers)

    return redirect('web:cart')


def checkout_view(request):
    """
    GET  /web/checkout/ → muestra resumen del carrito para confirmar
    POST /web/checkout/ → llama al endpoint de checkout y genera la orden
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    # Obtenemos el carrito actual para mostrar el resumen
    cart_resp = requests.get(f'{API_BASE}/cart/', headers=headers)
    cart = cart_resp.json() if cart_resp.status_code == 200 else None

    if request.method == 'POST':
        response = requests.post(f'{API_BASE}/orders/checkout/', headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Orden creada correctamente.')
            return redirect('web:orders')
        else:
            error = response.json().get('error', 'Error al procesar el checkout.')
            return render(request, 'web/checkout.html', {
                'cart': cart,
                'error': error
            })

    return render(request, 'web/checkout.html', {'cart': cart})


def orders_view(request):
    """
    GET /web/orders/ → historial de órdenes del usuario autenticado
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    response = requests.get(f'{API_BASE}/orders/', headers=headers)
    ordenes = response.json() if response.status_code == 200 else []

    return render(request, 'web/orders.html', {'ordenes': ordenes})


def order_detail_view(request, orden_id):
    """
    GET /web/orders/{id}/ → detalle de una orden específica
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    response = requests.get(f'{API_BASE}/orders/{orden_id}/', headers=headers)
    if response.status_code != 200:
        messages.error(request, 'Orden no encontrada.')
        return redirect('web:orders')

    orden = response.json()
    return render(request, 'web/order_detail.html', {'orden': orden})


def confirm_order_view(request, orden_id):
    """
    POST /web/orders/{id}/confirm/ → confirma el pago de una orden
    Llama al endpoint de confirmación simulada del Integrante 2.
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        response = requests.post(
            f'{API_BASE}/orders/{orden_id}/confirm/',
            headers=headers
        )

        if response.status_code == 200:
            messages.success(request, 'Pago confirmado. Tu orden está lista.')
        else:
            messages.error(request, 'Error al confirmar el pago.')

    return redirect('web:order_detail', orden_id=orden_id)