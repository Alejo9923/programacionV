import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps

def staff_required(view_func):
    """
    Decorador personalizado que verifica si el usuario tiene is_staff=True
    en la SESIÓN (guardado durante el login), en lugar de request.user.is_staff
    (que requeriría autenticación tradicional de Django, no JWT).

    Si no es staff o no hay sesión activa, redirige al login web.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('access_token'):
            messages.error(request, 'Necesitás iniciar sesión.')
            return redirect('web:login')

        if not request.session.get('is_staff'):
            messages.error(request, 'No tenés permisos para acceder al dashboard.')
            return redirect('web:catalog')

        return view_func(request, *args, **kwargs)

    return wrapper

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

            # Consultamos el perfil para saber si el usuario es staff
            # y así poder mostrar u ocultar el enlace al dashboard
            profile_resp = requests.get(
                f'{API_BASE}/auth/profile/',
                headers={'Authorization': f'Bearer {data["access"]}'}
            )
            if profile_resp.status_code == 200:
                profile_data = profile_resp.json()
                request.session['is_staff'] = profile_data.get('is_staff', False)
                request.session['user_id'] = profile_data.get('id')



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

    # Traemos las reseñas del producto desde la API.
    # Si falla (producto inexistente, error de red), usamos un dict vacío seguro.
    reviews_resp = requests.get(f'{API_BASE}/products/{producto_id}/reviews/')
    reviews_data = reviews_resp.json() if reviews_resp.status_code == 200 else {
        'rating_promedio': None,
        'total_resenas': 0,
        'resenas': [],
    }

    return render(request, 'web/product_detail.html', {
        'producto': producto,
        'reviews_data': reviews_data,
    })



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

@staff_required 
def dashboard_view(request):
    """
    GET /web/dashboard/ → panel principal del dashboard de staff.
    Solo accesible para usuarios con is_staff=True.
    @staff_required redirige al login del admin si no cumple la condición.
    """
    return render(request, 'web/dashboard/index.html')


@staff_required
def dashboard_categories_view(request):
    """
    GET  /web/dashboard/categories/ → lista categorías
    POST /web/dashboard/categories/ → crea una categoría nueva
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')

        response = requests.post(f'{API_BASE}/categories/', json={
            'nombre': nombre,
            'descripcion': descripcion
        }, headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Categoría creada correctamente.')
        else:
            messages.error(request, 'Error al crear la categoría.')

        return redirect('web:dashboard_categories')

    response = requests.get(f'{API_BASE}/categories/', headers=headers)
    categorias = response.json() if response.status_code == 200 else []

    return render(request, 'web/dashboard/categories.html', {'categorias': categorias})


@staff_required
def dashboard_category_delete_view(request, categoria_id):
    """
    POST /web/dashboard/categories/{id}/delete/ → elimina una categoría
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        response = requests.delete(f'{API_BASE}/categories/{categoria_id}/', headers=headers)
        if response.status_code == 204:
            messages.success(request, 'Categoría eliminada.')
        else:
            messages.error(request, 'No se pudo eliminar la categoría.')

    return redirect('web:dashboard_categories')


@staff_required
def dashboard_products_view(request):
    """
    GET  /web/dashboard/products/ → lista productos (todos, incluso inactivos)
    POST /web/dashboard/products/ → crea un producto nuevo
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        # Usamos requests con archivos porque el producto puede incluir una imagen
        files = {}
        if request.FILES.get('imagen'):
            imagen = request.FILES['imagen']
            files['imagen'] = (imagen.name, imagen.read(), imagen.content_type)

        data = {
            'nombre': request.POST.get('nombre'),
            'descripcion': request.POST.get('descripcion', ''),
            'precio_base': request.POST.get('precio_base'),
            'categoria': request.POST.get('categoria'),
            'activo': request.POST.get('activo') == 'on',
        }

        response = requests.post(
            f'{API_BASE}/products/',
            data=data,
            files=files if files else None,
            headers=headers
        )

        if response.status_code == 201:
            messages.success(request, 'Producto creado correctamente.')
        else:
            messages.error(request, f'Error al crear el producto: {response.text}')

        return redirect('web:dashboard_products')

    # Para el dashboard mostramos TODOS los productos, incluso inactivos.
    # El endpoint público filtra activo=True, así que pedimos con un parámetro extra
    # o iteramos: como la vista pública de la API ya filtra, usamos el admin token
    # que de todas formas solo ve lo que el queryset público permite.
    # Nota: si se necesita ver inactivos, se podría exponer un endpoint admin-only.
    response = requests.get(f'{API_BASE}/products/', headers=headers)
    categorias_resp = requests.get(f'{API_BASE}/categories/', headers=headers)

    productos = response.json() if response.status_code == 200 else []
    categorias = categorias_resp.json() if categorias_resp.status_code == 200 else []

    return render(request, 'web/dashboard/products.html', {
        'productos': productos,
        'categorias': categorias,
    })


@staff_required
def dashboard_product_edit_view(request, producto_id):
    """
    GET  /web/dashboard/products/{id}/edit/ → formulario de edición
    POST /web/dashboard/products/{id}/edit/ → actualiza el producto
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        files = {}
        if request.FILES.get('imagen'):
            imagen = request.FILES['imagen']
            files['imagen'] = (imagen.name, imagen.read(), imagen.content_type)

        data = {
            'nombre': request.POST.get('nombre'),
            'descripcion': request.POST.get('descripcion', ''),
            'precio_base': request.POST.get('precio_base'),
            'categoria': request.POST.get('categoria'),
            'activo': request.POST.get('activo') == 'on',
        }

        response = requests.put(
            f'{API_BASE}/products/{producto_id}/',
            data=data,
            files=files if files else None,
            headers=headers
        )

        if response.status_code == 200:
            messages.success(request, 'Producto actualizado.')
        else:
            messages.error(request, f'Error al actualizar: {response.text}')

        return redirect('web:dashboard_products')

    response = requests.get(f'{API_BASE}/products/{producto_id}/', headers=headers)
    categorias_resp = requests.get(f'{API_BASE}/categories/', headers=headers)

    if response.status_code != 200:
        messages.error(request, 'Producto no encontrado.')
        return redirect('web:dashboard_products')

    return render(request, 'web/dashboard/product_edit.html', {
        'producto': response.json(),
        'categorias': categorias_resp.json() if categorias_resp.status_code == 200 else [],
    })


@staff_required
def dashboard_product_delete_view(request, producto_id):
    """
    POST /web/dashboard/products/{id}/delete/ → elimina un producto
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        response = requests.delete(f'{API_BASE}/products/{producto_id}/', headers=headers)
        if response.status_code == 204:
            messages.success(request, 'Producto eliminado.')
        else:
            messages.error(request, 'No se pudo eliminar el producto.')

    return redirect('web:dashboard_products')


@staff_required
def dashboard_variants_view(request, producto_id):
    """
    GET  /web/dashboard/products/{producto_id}/variants/ → lista variantes del producto
    POST /web/dashboard/products/{producto_id}/variants/ → crea una variante nueva
    """
    headers = get_auth_headers(request)

    producto_resp = requests.get(f'{API_BASE}/products/{producto_id}/', headers=headers)
    if producto_resp.status_code != 200:
        messages.error(request, 'Producto no encontrado.')
        return redirect('web:dashboard_products')

    producto = producto_resp.json()

    if request.method == 'POST':
        response = requests.post(f'{API_BASE}/products/{producto_id}/variants/', json={
            'talla': request.POST.get('talla'),
            'color': request.POST.get('color'),
            'stock': request.POST.get('stock'),
            'precio_extra': request.POST.get('precio_extra', '0.00'),
        }, headers=headers)

        if response.status_code == 201:
            messages.success(request, 'Variante creada correctamente.')
        else:
            messages.error(request, f'Error al crear la variante: {response.text}')

        return redirect('web:dashboard_variants', producto_id=producto_id)

    return render(request, 'web/dashboard/variants.html', {
        'producto': producto,
        'variantes': producto.get('variantes', []),
    })


@staff_required
def dashboard_variant_edit_view(request, variante_id):
    """
    POST /web/dashboard/variants/{id}/edit/ → actualiza stock/precio de una variante
    """
    headers = get_auth_headers(request)

    if request.method == 'POST':
        response = requests.put(f'{API_BASE}/variants/{variante_id}/', json={
            'talla': request.POST.get('talla'),
            'color': request.POST.get('color'),
            'stock': request.POST.get('stock'),
            'precio_extra': request.POST.get('precio_extra'),
        }, headers=headers)

        if response.status_code == 200:
            messages.success(request, 'Variante actualizada.')
        else:
            messages.error(request, 'Error al actualizar la variante.')

    # Volvemos a la página de variantes del producto correspondiente
    variante_resp = requests.get(f'{API_BASE}/variants/{variante_id}/', headers=headers)
    producto_id = variante_resp.json().get('producto') if variante_resp.status_code == 200 else None

    return redirect('web:dashboard_variants', producto_id=producto_id)


@staff_required
def dashboard_variant_delete_view(request, variante_id):
    """
    POST /web/dashboard/variants/{id}/delete/ → elimina una variante
    """
    headers = get_auth_headers(request)

    # Necesitamos el producto_id antes de borrar, para poder redirigir después
    variante_resp = requests.get(f'{API_BASE}/variants/{variante_id}/', headers=headers)
    producto_id = variante_resp.json().get('producto') if variante_resp.status_code == 200 else None

    if request.method == 'POST':
        response = requests.delete(f'{API_BASE}/variants/{variante_id}/', headers=headers)
        if response.status_code == 204:
            messages.success(request, 'Variante eliminada.')
        else:
            messages.error(request, 'No se pudo eliminar la variante.')

    return redirect('web:dashboard_variants', producto_id=producto_id)

def create_review_view(request, producto_id):
    """
    POST /web/products/{id}/reviews/ → envía una reseña a la API.

    La API verifica que el usuario haya comprado el producto (orden 'paid').
    Si no compró, devuelve 403; si ya dejó una reseña, devuelve 400.
    En ambos casos mostramos el mensaje de error en el detalle del producto.
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comentario = request.POST.get('comentario')

        response = requests.post(
            f'{API_BASE}/products/{producto_id}/reviews/',
            json={'rating': int(rating), 'comentario': comentario},
            headers=headers,
        )

        if response.status_code == 201:
            messages.success(request, 'Reseña publicada.')
        else:
            # La API devuelve {'error': '...'} en 403 (no compró) y 400 (ya reseñó)
            error_msg = response.json().get('error', 'No se pudo publicar la reseña.')
            messages.error(request, error_msg)

    return redirect('web:product_detail', producto_id=producto_id)


def delete_review_view(request, review_id):
    """
    POST /web/reviews/{id}/delete/ → elimina una reseña propia.

    Usamos POST en lugar de DELETE porque los formularios HTML solo soportan
    GET y POST. El producto_id viene en el body para poder redirigir de vuelta
    al detalle del producto después de borrar.
    """
    headers = get_auth_headers(request)
    if not headers:
        return redirect('web:login')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')

        # Llamamos al endpoint DELETE de la API con el token del usuario.
        # La API verifica que el usuario sea el autor (403 si no lo es).
        response = requests.delete(f'{API_BASE}/reviews/{review_id}/', headers=headers)

        if response.status_code == 204:
            messages.success(request, 'Reseña eliminada.')
        else:
            messages.error(request, 'No se pudo eliminar la reseña.')

        if producto_id:
            return redirect('web:product_detail', producto_id=int(producto_id))

    return redirect('web:catalog')

