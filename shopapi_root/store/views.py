from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from django.db.utils import DatabaseError
from .db import call_procedure, call_function

def products_list(request):
    rows, _ = call_procedure('sp_products_list')
    return render(request, 'store/products_list.html', {'products': rows})

def product_add(request):
    with connection.cursor() as c:
        c.execute("SELECT category_id, name FROM categories ORDER BY name")
        categories = c.fetchall()
    if request.method == 'POST':
        try:
            _, out = call_procedure('sp_product_add',
                [request.POST['name'], int(request.POST['category_id']), 
                 float(request.POST['price']), int(request.POST['stock'])],
                out_count=1, fetch=False)
            messages.success(request, f"Товар добавлен (ID {out[0]})")
            return redirect('products_list')
        except DatabaseError as e:
            messages.error(request, f"Ошибка БД: {e}")
    return render(request, 'store/product_add.html', {'categories': categories})

def product_price(request, pk):
    if request.method == 'POST':
        try:
            call_procedure('sp_product_update_price', [pk, float(request.POST['price'])], fetch=False)
            messages.success(request, "Цена обновлена")
            return redirect('products_list')
        except DatabaseError as e:
            messages.error(request, f"Ошибка: {e}")
    return render(request, 'store/product_price.html', {'pk': pk})

def order_create(request):
    with connection.cursor() as c:
        c.execute("SELECT customer_id, first_name, last_name FROM customers ORDER BY last_name")
        customers = c.fetchall()
        
    if request.method == 'POST':
        if 'customer_id' not in request.POST:
            messages.error(request, "Ошибка: не выбран клиент. Возможно, список клиентов пуст.")
            return render(request, 'store/order_create.html', {'customers': customers})

        cid = int(request.POST['customer_id'])
        try:
            _, out = call_procedure('sp_order_create', [cid], out_count=1, fetch=False)
            messages.success(request, f"Заказ #{out[0]} создан")
            return redirect('order_detail', order_id=out[0])
        except DatabaseError as e:
            messages.error(request, f"Ошибка БД: {e}")
            
    return render(request, 'store/order_create.html', {'customers': customers})

def order_add_item(request, order_id):
    if request.method == 'POST':
        try:
            _, out = call_procedure('sp_order_add_item',
                [order_id, int(request.POST['product_id']), int(request.POST['quantity'])],
                out_count=2, fetch=False)
            success, msg = out[0], out[1]
            if success: messages.success(request, f"Позиция добавлена: {msg}")
            else: messages.error(request, msg)
        except DatabaseError as e:
            messages.error(request, f"Ошибка БД: {e}")
    return redirect('order_detail', order_id=order_id)

def order_detail(request, order_id):
    with connection.cursor() as c:
        c.execute("""SELECT oi.product_id, p.name, oi.quantity, oi.price, (oi.quantity*oi.price)
                     FROM order_items oi JOIN products p USING(product_id) WHERE oi.order_id=%s""", [order_id])
        items = c.fetchall()
        
        c.execute("SELECT order_id, customer_id, created_at, total FROM orders WHERE order_id=%s", [order_id])
        order = c.fetchone()
        
        c.execute("SELECT product_id, name, stock FROM products ORDER BY name")
        products = c.fetchall()
        
    return render(request, 'store/order_detail.html', 
                  {'order': order, 'items': items, 'order_id': order_id, 'products': products})

def customer_orders(request, pk):
    rows, _ = call_procedure('sp_customer_orders', [pk])
    return render(request, 'store/customer_orders.html', {'orders': rows, 'customer_id': pk})

def category_stats(request):
    rows, _ = call_procedure('sp_category_stats')
    top = max((r[3] for r in rows), default=0)
    return render(request, 'store/category_stats.html', {'rows': rows, 'top_revenue': top})

def discount_view(request):
    result = None
    
    with connection.cursor() as c:
        c.execute("SELECT customer_id, first_name, last_name FROM customers ORDER BY last_name")
        customers = c.fetchall()

    if request.method == 'POST':
        try:
            cid = int(request.POST['customer_id'])
            amount = float(request.POST['amount'])
            percent = float(call_function('fn_customer_discount', [cid, amount]))
            total = round(amount * (1 - percent / 100), 2)
            result = {'customer_id': cid, 'amount': amount, 
                      'percent': percent, 'total': total}
        except (DatabaseError, ValueError) as e:
            messages.error(request, f"Ошибка: {e}")
            
    return render(request, 'store/discount.html', {'result': result, 'customers': customers})