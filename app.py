import streamlit as st
import mysql.connector
import pandas as pd


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="ShopSphere",
    page_icon="🛒",
    layout="wide"
)
st.markdown("""
<style>

.stApp {
    background-color: #0f1117;
    color: white;
}

h1, h2, h3 {
    color: white;
}

.stButton > button {
    background-color: #1f2937;
    color: white;
    border-radius: 8px;
    border: 1px solid #374151;
}

.stButton > button:hover {
    background-color: #374151;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="ecommerce"
    )


# =====================================================
# DATABASE FUNCTION
# =====================================================

def execute_query(query, values=(), fetch=False):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(query, values)

    if fetch:

        result = cursor.fetchall()

    else:

        conn.commit()
        result = cursor.lastrowid

    cursor.close()
    conn.close()

    return result


# =====================================================
# SESSION STATE
# =====================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Products"

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None


# =====================================================
# LOGIN
# =====================================================

def login_page():

    st.title("🛒 ShopSphere")

    st.subheader("Login")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        user = execute_query(
            """
            SELECT *
            FROM users
            WHERE email=%s
            AND password=%s
            """,
            (email.strip(), password),
            True
        )

        if user:

            st.session_state.user = user[0]
            st.session_state.page = "Products"

            st.success("Login successful!")

            st.rerun()

        else:

            st.error("Invalid email or password")


# =====================================================
# REGISTER
# =====================================================

def register_page():

    st.subheader("Create New Account")

    name = st.text_input(
        "Name",
        key="reg_name"
    )

    email = st.text_input(
        "Email",
        key="reg_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="reg_password"
    )

    if st.button("Register"):

        if name == "" or email == "" or password == "":

            st.error(
                "Please fill all fields"
            )

            return

        try:

            execute_query(
                """
                INSERT INTO users
                (name,email,password,role)
                VALUES (%s,%s,%s,'User')
                """,
                (
                    name,
                    email,
                    password
                )
            )

            st.success(
                "Account created successfully!"
            )

        except:

            st.error(
                "Email already exists"
            )


# =====================================================
# PRODUCTS
# =====================================================

def products_page():

    st.title("🛍️ Product Catalog")

    # Search

    search = st.text_input(
        "🔎 Search Product"
    )

    # Category filter

    categories = execute_query(
        """
        SELECT DISTINCT category
        FROM products
        """,
        fetch=True
    )

    category_list = ["All"]

    for category in categories:

        category_list.append(
            category["category"]
        )

    selected_category = st.selectbox(
        "Filter by Category",
        category_list
    )

    # Query

    query = """
        SELECT *
        FROM products
        WHERE 1=1
    """

    values = []

    if search:

        query += """
            AND name LIKE %s
        """

        values.append(
            "%" + search + "%"
        )

    if selected_category != "All":

        query += """
            AND category=%s
        """

        values.append(
            selected_category
        )

    products = execute_query(
        query,
        tuple(values),
        True
    )

    if not products:

        st.warning(
            "No products found."
        )

        return

    # Product cards

    columns = st.columns(3)

    for index, product in enumerate(products):

        with columns[index % 3]:

            st.subheader(
                product["name"]
            )

            st.write(
                product["description"]
            )

            st.write(
                f"### ₹{product['price']}"
            )

            st.write(
                f"Stock: {product['stock']}"
            )

            if st.button(
                "View Details",
                key=f"view_{product['product_id']}"
            ):

                st.session_state.selected_product = product

                st.session_state.page = "Details"

                st.rerun()


# =====================================================
# PRODUCT DETAILS
# =====================================================

def product_details():

    product = st.session_state.selected_product

    st.title("📦 Product Details")

    st.header(
        product["name"]
    )

    st.write(
        product["description"]
    )

    st.write(
        f"**Category:** {product['category']}"
    )

    st.write(
        f"**Price:** ₹{product['price']}"
    )

    st.write(
        f"**Available Stock:** {product['stock']}"
    )

    if product["stock"] <= 0:

        st.error(
            "Out of stock"
        )

        return

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        max_value=product["stock"],
        value=1
    )

    # Add cart

    if st.button("🛒 Add to Cart"):

        user_id = st.session_state.user["user_id"]

        existing = execute_query(
            """
            SELECT *
            FROM cart
            WHERE user_id=%s
            AND product_id=%s
            """,
            (
                user_id,
                product["product_id"]
            ),
            True
        )

        if existing:

            execute_query(
                """
                UPDATE cart
                SET quantity = quantity + %s
                WHERE user_id=%s
                AND product_id=%s
                """,
                (
                    quantity,
                    user_id,
                    product["product_id"]
                )
            )

        else:

            execute_query(
                """
                INSERT INTO cart
                (user_id,product_id,quantity)
                VALUES (%s,%s,%s)
                """,
                (
                    user_id,
                    product["product_id"],
                    quantity
                )
            )

        st.success(
            "Product added to cart!"
        )

    # Wishlist

    if st.button("❤️ Add to Wishlist"):

        user_id = st.session_state.user["user_id"]

        existing = execute_query(
            """
            SELECT *
            FROM wishlist
            WHERE user_id=%s
            AND product_id=%s
            """,
            (
                user_id,
                product["product_id"]
            ),
            True
        )

        if existing:

            st.info(
                "Already in wishlist."
            )

        else:

            execute_query(
                """
                INSERT INTO wishlist
                (user_id,product_id)
                VALUES (%s,%s)
                """,
                (
                    user_id,
                    product["product_id"]
                )
            )

            st.success(
                "Added to wishlist!"
            )


# =====================================================
# CART
# =====================================================

def cart_page():

    st.title("🛒 Shopping Cart")

    user_id = st.session_state.user["user_id"]

    cart = execute_query(
        """
        SELECT
            cart.cart_id,
            cart.quantity,
            products.product_id,
            products.name,
            products.price,
            products.stock
        FROM cart

        JOIN products
        ON cart.product_id = products.product_id

        WHERE cart.user_id=%s
        """,
        (user_id,),
        True
    )

    if not cart:

        st.info(
            "Your cart is empty."
        )

        return

    total = 0

    for item in cart:

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.write(
                f"**{item['name']}**"
            )

        with col2:

            st.write(
                f"₹{item['price']}"
            )

        with col3:

            new_quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=item["stock"],
                value=item["quantity"],
                key=f"qty_{item['cart_id']}"
            )

            if new_quantity != item["quantity"]:

                execute_query(
                    """
                    UPDATE cart
                    SET quantity=%s
                    WHERE cart_id=%s
                    """,
                    (
                        new_quantity,
                        item["cart_id"]
                    )
                )

                st.rerun()

        with col4:

            if st.button(
                "🗑️ Delete",
                key=f"delete_{item['cart_id']}"
            ):

                execute_query(
                    """
                    DELETE FROM cart
                    WHERE cart_id=%s
                    """,
                    (item["cart_id"],)
                )

                st.rerun()

        total += (
            float(item["price"])
            * item["quantity"]
        )

    st.divider()

    st.subheader(
        f"Total: ₹{total:.2f}"
    )

    if st.button("💳 Go to Checkout"):

        st.session_state.page = "Checkout"

        st.rerun()


# =====================================================
# WISHLIST
# =====================================================

def wishlist_page():

    st.title("❤️ My Wishlist")

    user_id = st.session_state.user["user_id"]

    wishlist = execute_query(
        """
        SELECT
            wishlist.wishlist_id,
            products.*
        FROM wishlist

        JOIN products
        ON wishlist.product_id = products.product_id

        WHERE wishlist.user_id=%s
        """,
        (user_id,),
        True
    )

    if not wishlist:

        st.info(
            "Your wishlist is empty."
        )

        return

    for item in wishlist:

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"**{item['name']}**"
            )

        with col2:

            st.write(
                f"₹{item['price']}"
            )

        with col3:

            if st.button(
                "Remove",
                key=f"remove_wish_{item['wishlist_id']}"
            ):

                execute_query(
                    """
                    DELETE FROM wishlist
                    WHERE wishlist_id=%s
                    """,
                    (item["wishlist_id"],)
                )

                st.rerun()


# =====================================================
# CHECKOUT
# =====================================================

def checkout_page():

    st.title("💳 Checkout")

    user_id = st.session_state.user["user_id"]

    cart = execute_query(
        """
        SELECT
            cart.product_id,
            cart.quantity,
            products.name,
            products.price,
            products.stock

        FROM cart

        JOIN products
        ON cart.product_id = products.product_id

        WHERE cart.user_id=%s
        """,
        (user_id,),
        True
    )

    if not cart:

        st.warning(
            "Your cart is empty."
        )

        return

    total = 0

    st.subheader(
        "Order Summary"
    )

    for item in cart:

        amount = (
            float(item["price"])
            * item["quantity"]
        )

        total += amount

        st.write(
            f"{item['name']} × "
            f"{item['quantity']} = ₹{amount:.2f}"
        )

    st.divider()

    st.subheader(
        f"Total: ₹{total:.2f}"
    )

    address = st.text_area(
        "Delivery Address"
    )

    if st.button("Place Order"):

        if address == "":

            st.error(
                "Please enter your address."
            )

            return

        # Check stock

        for item in cart:

            if item["quantity"] > item["stock"]:

                st.error(
                    f"Not enough stock for {item['name']}"
                )

                return

        # Create order

        order_id = execute_query(
            """
            INSERT INTO orders
            (user_id,total_amount,address)
            VALUES (%s,%s,%s)
            """,
            (
                user_id,
                total,
                address
            )
        )

        # Insert order items

        for item in cart:

            execute_query(
                """
                INSERT INTO order_items
                (order_id,product_id,quantity,price)
                VALUES (%s,%s,%s,%s)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["price"]
                )
            )

            # Reduce stock

            execute_query(
                """
                UPDATE products
                SET stock = stock - %s
                WHERE product_id=%s
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )

        # Clear cart

        execute_query(
            """
            DELETE FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        st.success(
            f"🎉 Order #{order_id} placed successfully!"
        )


# =====================================================
# ORDER HISTORY
# =====================================================

def orders_page():

    st.title("📋 Order History")

    user_id = st.session_state.user["user_id"]

    orders = execute_query(
        """
        SELECT *
        FROM orders

        WHERE user_id=%s

        ORDER BY order_date DESC
        """,
        (user_id,),
        True
    )

    if not orders:

        st.info(
            "You have not placed any orders."
        )

        return

    for order in orders:

        st.subheader(
            f"Order #{order['order_id']}"
        )

        st.write(
            f"Date: {order['order_date']}"
        )

        st.write(
            f"Total: ₹{order['total_amount']}"
        )

        st.write(
            f"Status: **{order['order_status']}**"
        )

        # Tracking

        if order["order_status"] != "Cancelled":

            st.progress(
                {
                    "Pending": 0.2,
                    "Confirmed": 0.4,
                    "Shipped": 0.6,
                    "Out for Delivery": 0.8,
                    "Delivered": 1.0
                }.get(
                    order["order_status"],
                    0.2
                )
            )

        # Cancel

        if order["order_status"] in [
            "Pending",
            "Confirmed"
        ]:

            if st.button(
                "❌ Cancel Order",
                key=f"cancel_{order['order_id']}"
            ):

                execute_query(
                    """
                    UPDATE orders

                    SET order_status='Cancelled'

                    WHERE order_id=%s
                    """,
                    (order["order_id"],)
                )

                st.success(
                    "Order cancelled."
                )

                st.rerun()

        st.divider()


# =====================================================
# ADMIN DASHBOARD
# =====================================================

def admin_page():

    st.title("👨‍💼 Admin Dashboard")

    # -------------------------------------------------
    # PRODUCT MANAGEMENT
    # -------------------------------------------------

    st.header("📦 Product Management")

    products = execute_query(
        """
        SELECT *
        FROM products
        """,
        fetch=True
    )

    if products:

        df = pd.DataFrame(products)

        st.dataframe(
            df,
            use_container_width=True
        )

    # Add product

    st.subheader("➕ Add Product")

    name = st.text_input(
        "Product Name",
        key="admin_name"
    )

    description = st.text_area(
        "Description",
        key="admin_description"
    )

    category = st.text_input(
        "Category",
        key="admin_category"
    )

    price = st.number_input(
        "Price",
        min_value=0.0,
        key="admin_price"
    )

    stock = st.number_input(
        "Stock",
        min_value=0,
        key="admin_stock"
    )

    if st.button("Add Product"):

        execute_query(
            """
            INSERT INTO products
            (name,description,category,price,stock)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                name,
                description,
                category,
                price,
                stock
            )
        )

        st.success(
            "Product added!"
        )

        st.rerun()

    # -------------------------------------------------
    # DELETE PRODUCT
    # -------------------------------------------------

    st.subheader("🗑️ Delete Product")

    product_list = execute_query(
        """
        SELECT product_id,name
        FROM products
        """,
        fetch=True
    )

    if product_list:

        product_names = {
            p["name"]: p["product_id"]
            for p in product_list
        }

        selected_product = st.selectbox(
            "Select Product",
            list(product_names.keys())
        )

        if st.button("Delete Product"):

            product_id = product_names[
                selected_product
            ]

            execute_query(
                """
                DELETE FROM products
                WHERE product_id=%s
                """,
                (product_id,)
            )

            st.success(
                "Product deleted."
            )

            st.rerun()

    # -------------------------------------------------
    # ORDER MANAGEMENT
    # -------------------------------------------------

    st.header("📋 Order Management")

    orders = execute_query(
        """
        SELECT
            orders.order_id,
            users.name,
            orders.total_amount,
            orders.order_status,
            orders.order_date

        FROM orders

        JOIN users
        ON orders.user_id = users.user_id

        ORDER BY orders.order_date DESC
        """,
        fetch=True
    )

    for order in orders:

        st.write(
            f"**Order #{order['order_id']}** "
            f"| User: {order['name']} "
            f"| ₹{order['total_amount']}"
        )

        status_options = [
            "Pending",
            "Confirmed",
            "Shipped",
            "Out for Delivery",
            "Delivered",
            "Cancelled"
        ]

        current_index = status_options.index(
            order["order_status"]
        )

        status = st.selectbox(
            "Order Status",
            status_options,
            index=current_index,
            key=f"admin_status_{order['order_id']}"
        )

        if st.button(
            "Update Status",
            key=f"update_{order['order_id']}"
        ):

            execute_query(
                """
                UPDATE orders

                SET order_status=%s

                WHERE order_id=%s
                """,
                (
                    status,
                    order["order_id"]
                )
            )

            st.success(
                "Order status updated!"
            )

            st.rerun()

        st.divider()


# =====================================================
# SIDEBAR
# =====================================================

def sidebar():

    st.sidebar.title("🛒 ShopSphere")

    st.sidebar.write(
        f"Welcome, "
        f"**{st.session_state.user['name']}**"
    )

    st.sidebar.write(
        f"Role: {st.session_state.user['role']}"
    )

    st.sidebar.divider()

    if st.sidebar.button("🏠 Products"):

        st.session_state.page = "Products"

        st.rerun()

    if st.sidebar.button("🛒 Cart"):

        st.session_state.page = "Cart"

        st.rerun()

    if st.sidebar.button("❤️ Wishlist"):

        st.session_state.page = "Wishlist"

        st.rerun()

    if st.sidebar.button("📋 Orders"):

        st.session_state.page = "Orders"

        st.rerun()

    if st.session_state.user["role"] == "Admin":

        if st.sidebar.button(
            "👨‍💼 Admin Dashboard"
        ):

            st.session_state.page = "Admin"

            st.rerun()

    st.sidebar.divider()

    if st.sidebar.button("Logout"):

        st.session_state.user = None

        st.session_state.page = "Products"

        st.rerun()


# =====================================================
# MAIN PROGRAM
# =====================================================

if st.session_state.user is None:

    login_page()

    st.divider()

    register_page()

else:

    sidebar()

    if st.session_state.page == "Products":

        products_page()

    elif st.session_state.page == "Details":

        product_details()

    elif st.session_state.page == "Cart":

        cart_page()

    elif st.session_state.page == "Wishlist":

        wishlist_page()

    elif st.session_state.page == "Checkout":

        checkout_page()

    elif st.session_state.page == "Orders":

        orders_page()

    elif st.session_state.page == "Admin":

        admin_page()