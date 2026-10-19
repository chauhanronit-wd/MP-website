import os
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    jsonify,
    url_for

    )
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory
app = Flask(__name__)

app.secret_key = "IndustrialLaundry@2026#SecureKey"

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

BROCHURE_UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "brochures"
)

os.makedirs(
    BROCHURE_UPLOAD_FOLDER,
    exist_ok=True
)

app.config[
    'BROCHURE_UPLOAD_FOLDER'
] = BROCHURE_UPLOAD_FOLDER

PRODUCT_UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "products"
)

GALLERY_UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "gallery"
)

os.makedirs(
    PRODUCT_UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    GALLERY_UPLOAD_FOLDER,
    exist_ok=True
)

app.config[
    'PRODUCT_UPLOAD_FOLDER'
] = PRODUCT_UPLOAD_FOLDER

app.config[
    'GALLERY_UPLOAD_FOLDER'
] = GALLERY_UPLOAD_FOLDER


from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_otp(email, otp):
    sender_email = "ronyyy2527@gmail.com"
    app_password = "jtwfgfmrzjloowdg"

    subject = "Industrial CRM OTP"
    body = f"""
Hello,

Your OTP for Industrial Laundry ERP & CRM is:

{otp}

Do not share this OTP with anyone.

Thank You
Industrial Laundry ERP
"""

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(message)
        server.quit()
        return True

    except Exception as e:
        print("SMTP Error:", e)
        return False

def generate_otp():
    return str(random.randint(100000, 999999))


def save_otp(email):

    otp = str(random.randint(100000, 999999))

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM otp_verification
    WHERE email=?
    """, (email,))

    expiry = datetime.now() + timedelta(minutes=5)

    cursor.execute("""
    INSERT INTO otp_verification
    (
        email,
        otp,
        expires_at,
        attempts,
        verified
    )
    VALUES
    (
        ?, ?, ?, 0, 0
    )
    """,
    (
        email,
        otp,
        expiry
    ))

    conn.commit()
    conn.close()

    return otp

@app.route("/send-email-otp", methods=["POST"])
def send_email_otp():

    try:

        email = request.form.get("email", "").strip().lower()

        if email == "":
            return jsonify({
                "status": "error",
                "message": "Email Required"
            })

        conn = sqlite3.connect("industrial.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        )

        existing = cursor.fetchone()

        conn.close()

        if existing:
            return jsonify({
                "status": "error",
                "message": "Email already registered"
            })

        otp = save_otp(email)

        sent = send_otp(email, otp)

        if sent:

            return jsonify({
                "status": "success"
            })

        return jsonify({
            "status": "error",
            "message": "OTP Send Failed"
        })

    except Exception as e:

        print(e)

        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/')
def home():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Create table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS featured_products (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         title TEXT NOT NULL,
                                                         image TEXT NOT NULL,
                                                         featured INTEGER DEFAULT 1
        )
    """)

    conn.commit()

    # Get featured products
    cursor.execute("""
        SELECT *
        FROM featured_products
        WHERE featured = 1
    """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "home.html",
        products=products
    )

@app.route('/products')
def products():

    search = request.args.get(
        'search',
        ''
    ).strip()

    category = request.args.get(
        'category',
        ''
    ).strip()

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if category:

        cursor.execute("""
            SELECT
                products.*,
                categories.category_name
            FROM products
            LEFT JOIN categories
                ON products.category_id =
                   categories.id
            WHERE categories.category_name = ?
            ORDER BY products.id DESC
        """, (category,))

    elif search:

        cursor.execute("""
            SELECT
                products.*,
                categories.category_name
            FROM products
            LEFT JOIN categories
                ON products.category_id =
                   categories.id
            WHERE
                products.product_name LIKE ?
                OR products.capacity LIKE ?
            ORDER BY products.id DESC
        """, (
            '%' + search + '%',
            '%' + search + '%'
        ))

    else:

        cursor.execute("""
            SELECT
                products.*,
                categories.category_name
            FROM products
            LEFT JOIN categories
                ON products.category_id =
                   categories.id
            ORDER BY products.id DESC
        """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        'products.html',
        products=products
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = sqlite3.connect("industrial.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    users.*,
                    departments.department_name,
                    roles.role_name
                FROM users
                LEFT JOIN departments
                    ON users.department_id = departments.id
                LEFT JOIN roles
                    ON users.role_id = roles.id
                WHERE users.username = ?
            """, (username,))

            user = cursor.fetchone()

        except sqlite3.Error:
            app.logger.exception("Login database error")
            error = "Unable to check login details. Please try again."
            user = None

        finally:
            conn.close()

        if error is None:
            if user is None:
                error = "Invalid Username"

            elif not check_password_hash(user["password"], password):
                error = "Invalid Password"

            elif user["email_verified"] == 0:
                error = "Please verify your email first."

            elif user["is_verified"] == 0:
                error = "Please verify your email first."

            elif user["account_status"] != "Active":
                error = "Your account is waiting for Admin Approval."

            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role_name"]
                session["department"] = user["department_name"]

                if user["role_name"] == "Admin":
                    return redirect("/dashboard")

                elif user["role_name"] == "Manager":
                    return redirect("/manager-dashboard")

                return redirect("/dashboard")

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route('/categories')
def categories():

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM categories
        ORDER BY id DESC
        """
    )

    categories = cursor.fetchall()

    conn.close()

    return render_template(
        "categories.html",
        categories=categories
    )

@app.route(
'/add-category',
methods=['GET','POST']
)
def add_category():

    if request.method == 'POST':

        category_name = request.form[
            'category_name'
        ]

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO categories
            (
            category_name
            )
            VALUES
            (
            ?
            )
            """,
            (category_name,)
        )

        conn.commit()
        conn.close()

        return redirect(
            '/categories'
        )

    return render_template(
        'add_category.html'
    )

@app.route(
'/edit-category/<int:id>',
methods=['GET','POST']
)
def edit_category(id):

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if request.method == 'POST':

        cursor.execute(
            """
            UPDATE categories
            SET category_name=?
            WHERE id=?
            """,
            (
                request.form['category_name'],
                id
            )
        )

        conn.commit()
        conn.close()

        return redirect(
            '/categories'
        )

    cursor.execute(
        """
        SELECT *
        FROM categories
        WHERE id=?
        """,
        (id,)
    )

    category = cursor.fetchone()

    conn.close()

    return render_template(
        'edit_category.html',
        category=category
    )

@app.route(
'/delete-category/<int:id>'
)
def delete_category(id):

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM categories
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        '/categories'
    )


@app.route('/dashboard')
def dashboard():

    if "user_id" not in session:
        return redirect('/login')

    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect("/manager-dashboard")

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    total_products = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM gallery"
    )
    total_gallery = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM gallery_categories WHERE category='Machine Photos'"
    )
    total_machine_photos = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM gallery_categories WHERE category='Installation Photos'"
    )
    total_installation_photos = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM inquiries"
    )

    total_inquiries = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM contact_inquiries"
    )

    total_contact_inquiries = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM inquiries
        WHERE status='Pending'
        """
    )

    pending_leads = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM inquiries
        WHERE status = 'Approved'
        """
    )

    approved_leads = cursor.fetchone()[0]

    # ---------------------------------
    # CATALOG LEADS TABLE / COLUMN
    # ---------------------------------

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS catalog_leads
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       company
                       TEXT,
                       email
                       TEXT
                       NOT
                       NULL,
                       phone
                       TEXT
                       NOT
                       NULL,
                       city
                       TEXT,
                       created_at
                       TEXT
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # Check existing columns
    cursor.execute("""
        PRAGMA table_info(catalog_leads)
    """)

    catalog_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    # Add opened_at only if missing
    if 'opened_at' not in catalog_columns:
        cursor.execute("""
                       ALTER TABLE catalog_leads
                           ADD COLUMN opened_at TEXT
                       """)

    conn.commit()
    # ---------------------------------
    # CATALOG OPENS
    # ---------------------------------

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS catalog_leads
                   (

                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,

                       name
                       TEXT
                       NOT
                       NULL,

                       company
                       TEXT,

                       email
                       TEXT
                       NOT
                       NULL,

                       phone
                       TEXT
                       NOT
                       NULL,

                       city
                       TEXT,

                       created_at
                       TEXT
                       DEFAULT
                       CURRENT_TIMESTAMP,

                       opened_at
                       TEXT

                   )
                   """)

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM catalog_leads
                   WHERE opened_at IS NOT NULL
                   """)

    catalog_opens = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',

        total_products=total_products,

        total_gallery=total_gallery,

        total_machine_photos=total_machine_photos,

        total_installation_photos=total_installation_photos,

        total_inquiries=total_inquiries,

        pending_leads=pending_leads,

        approved_leads=approved_leads,

    total_contact_inquiries = total_contact_inquiries,

    catalog_opens = catalog_opens
    )

@app.route("/manager-dashboard")
def manager_dashboard():

    if "user_id" not in session:

        return redirect("/login")

    if session.get("role") != "Manager":

        flash("Access Denied", "danger")

        return redirect("/dashboard")

    return render_template(
        "manager_dashboard.html"
    )


@app.route('/add-product', methods=['GET', 'POST'])
def add_product():

    if "user_id" not in session:
        return redirect('/login')

    # -----------------------------
    # GET - LOAD CATEGORIES
    # -----------------------------
    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM categories
        ORDER BY id DESC
    """)

    categories = cursor.fetchall()
    conn.close()

    # -----------------------------
    # POST - ADD PRODUCT
    # -----------------------------
    if request.method == 'POST':

        product_name = request.form.get(
            'product_name', ''
        ).strip()

        category_id = request.form.get(
            'category_id', ''
        ).strip()

        capacity = request.form.get(
            'capacity', ''
        ).strip()

        material = request.form.get(
            'material', ''
        ).strip()

        power = request.form.get(
            'power', ''
        ).strip()

        voltage = request.form.get(
            'voltage', ''
        ).strip()

        warranty = request.form.get(
            'warranty', ''
        ).strip()

        description = request.form.get(
            'description', ''
        ).strip()

        youtube_url = request.form.get(
            'youtube_url', ''
        ).strip()

        image = request.files.get('image')
        brochure = request.files.get('brochure')

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if not product_name:
            flash(
                "Product name is required.",
                "danger"
            )
            return redirect('/add-product')

        if not category_id:
            flash(
                "Please select a category.",
                "danger"
            )
            return redirect('/add-product')

        if not image or not image.filename:
            flash(
                "Product image is required.",
                "danger"
            )
            return redirect('/add-product')

        # -----------------------------
        # DUPLICATE CHECK
        # -----------------------------
        conn = sqlite3.connect("industrial.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM products
            WHERE LOWER(TRIM(product_name))
                  = LOWER(TRIM(?))
            AND category_id = ?
            LIMIT 1
        """, (
            product_name,
            category_id
        ))

        existing_product = cursor.fetchone()

        if existing_product:
            conn.close()

            flash(
                "This product already exists.",
                "warning"
            )

            return redirect('/admin-products')

        # -----------------------------
        # SAVE PRODUCT IMAGE
        # -----------------------------
        filename = secure_filename(
            image.filename
        )

        image.save(
            os.path.join(
                app.config[
                    'PRODUCT_UPLOAD_FOLDER'
                ],
                filename
            )
        )

        # -----------------------------
        # SAVE BROCHURE
        # -----------------------------
        brochure_filename = ""

        if brochure and brochure.filename:

            brochure_filename = secure_filename(
                brochure.filename
            )

            brochure.save(
                os.path.join(
                    app.config[
                        'BROCHURE_UPLOAD_FOLDER'
                    ],
                    brochure_filename
                )
            )

        # -----------------------------
        # INSERT PRODUCT
        # -----------------------------
        cursor.execute("""
            INSERT INTO products
            (
                product_name,
                category_id,
                capacity,
                material,
                power,
                voltage,
                warranty,
                description,
                youtube_url,
                image,
                brochure
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            product_name,
            category_id,
            capacity,
            material,
            power,
            voltage,
            warranty,
            description,
            youtube_url,
            filename,
            brochure_filename
        ))

        conn.commit()
        conn.close()

        flash(
            "Product added successfully.",
            "success"
        )

        return redirect('/admin-products')

    return render_template(
        'add_product.html',
        categories=categories
    )

@app.route(
'/uploads/brochures/<filename>'
)
def brochure_file(filename):

    return send_from_directory(
        app.config[
            'BROCHURE_UPLOAD_FOLDER'
        ],
        filename
    )

@app.route(
'/uploads/products/<filename>'
)
def product_image(filename):

    return send_from_directory(
        app.config[
            'PRODUCT_UPLOAD_FOLDER'
        ],
        filename
    )
@app.route('/about')
def about():

    return render_template(
        'about.html'
    )


@app.route(
'/contact',
methods=['GET','POST']
)
def contact():

    if request.method == 'POST':

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO
            contact_inquiries

            (
            name,
            email,
            phone,
            message
            )

            VALUES
            (
            ?, ?, ?, ?
            )
            """,

            (
                request.form['name'],
                request.form['email'],
                request.form['phone'],
                request.form['message']
            )
        )

        conn.commit()

        conn.close()

        return redirect(
            '/contact'
        )

    return render_template(
        'contact.html'
    )

@app.route('/contact-inquiries')
def contact_inquiries():
    if "user_id" not in session:
        return redirect('/login')

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM contact_inquiries
        ORDER BY id DESC
        """
    )

    inquiries = cursor.fetchall()

    for i in inquiries:
        print(dict(i))

    conn.close()

    return render_template(
        'contact_inquiries.html',
        inquiries=inquiries
    )

@app.route(
'/contact-inquiry/<int:id>'
)
def contact_inquiry_details(id):

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM contact_inquiries
        WHERE id=?
        """,
        (id,)
    )

    inquiry = cursor.fetchone()

    conn.close()

    return render_template(
        'contact_inquiry_details.html',
        inquiry=inquiry
    )

@app.route(
'/delete-contact-inquiry/<int:id>'
)
def delete_contact_inquiry(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM contact_inquiries
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        '/contact-inquiries'
    )


@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/product/<int:id>')
def product_details(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # =====================================================
    # GET CURRENT PRODUCT
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=?
        """,
        (id,)
    )

    product = cursor.fetchone()

    if product is None:
        conn.close()
        return f"Product ID {id} Not Found"


    # =====================================================
    # RELATED PRODUCTS
    # =====================================================

    related_products = []

    # First: same category
    cursor.execute(
        """
        SELECT
            id,
            product_name,
            image,
            category_id,
            capacity
        FROM products
        WHERE id != ?
          AND category_id = ?
        ORDER BY id DESC
        LIMIT 4
        """,
        (
            product["id"],
            product["category_id"]
        )
    )

    related_products = cursor.fetchall()


    # If no same-category products,
    # show latest products
    if not related_products:

        cursor.execute(
            """
            SELECT
                id,
                product_name,
                image,
                category_id,
                capacity
            FROM products
            WHERE id != ?
            ORDER BY id DESC
            LIMIT 4
            """,
            (product["id"],)
        )

        related_products = cursor.fetchall()


    # =====================================================
    # CONVERT PRODUCT TO DICT
    # =====================================================

    product = dict(product)


    # =====================================================
    # YOUTUBE URL
    # =====================================================

    youtube = product.get("youtube_url")

    if youtube:

        youtube = youtube.strip()

        if "youtu.be/" in youtube:

            video_id = (
                youtube
                .split("youtu.be/")[1]
                .split("?")[0]
            )

        elif "watch?v=" in youtube:

            video_id = (
                youtube
                .split("watch?v=")[1]
                .split("&")[0]
            )

        elif "embed/" in youtube:

            video_id = (
                youtube
                .split("embed/")[1]
                .split("?")[0]
            )

        else:

            video_id = youtube

        product["embed_url"] = (
            f"https://www.youtube.com/embed/{video_id}"
        )

    else:

        product["embed_url"] = ""


    # =====================================================
    # PRODUCT GALLERY
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM product_gallery
        WHERE product_id=?
        """,
        (id,)
    )

    gallery = cursor.fetchall()


    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    conn.close()


    # =====================================================
    # RENDER
    # =====================================================

    return render_template(
        "product_details.html",
        product=product,
        gallery=gallery,
        related_products=related_products
    )

@app.context_processor
def inject_products():

    conn = sqlite3.connect("industrial.db")

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, product_name FROM products"
    )

    products_menu = cursor.fetchall()

    conn.close()

    return dict(
        products_menu=products_menu
    )

@app.context_processor
def inject_categories():

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM categories
        """
    )

    categories = cursor.fetchall()

    conn.close()

    return dict(
        categories_menu=categories
    )

@app.route(
'/edit-product/<int:id>',
methods=['GET','POST']
)
def edit_product(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if request.method == 'POST':

        cursor.execute(
            "SELECT * FROM products WHERE id=?",
            (id,)
        )

        product = cursor.fetchone()

        image_filename = product['image']

        brochure_filename = product['brochure']

        image = request.files['image']

        if image and image.filename:
            image_filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config[
                        'PRODUCT_UPLOAD_FOLDER'
                    ],
                    image_filename
                )
            )

        brochure = request.files['brochure']

        if brochure and brochure.filename:
            brochure_filename = secure_filename(
                brochure.filename
            )

            brochure.save(
                os.path.join(
                    app.config[
                        'BROCHURE_UPLOAD_FOLDER'
                    ],
                    brochure_filename
                )
            )

        cursor.execute(
            """
            UPDATE products

            SET product_name=?,
                category_id=?,
                capacity=?,
                material=?,
                power=?,
                voltage=?,
                warranty=?,
                description=?,
                youtube_url=?,
                image=?,
                brochure=?

            WHERE id = ?
            """,

            (
                request.form['product_name'],
                request.form['category_id'],
                request.form['capacity'],
                request.form['material'],
                request.form['power'],
                request.form['voltage'],
                request.form['warranty'],
                request.form['description'],
                request.form['youtube_url'],
                image_filename,
                brochure_filename,
                id
            )
        )

        conn.commit()

        conn.close()

        return redirect(
            '/admin-products'
        )

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    )

    product = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM categories
        """
    )

    categories = cursor.fetchall()

    conn.close()

    return render_template(
        'edit_product.html',
        product=product,
        categories=categories
    )

@app.route(
'/remove-product-video/<int:id>'
)
def remove_product_video(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products

        SET youtube_url=''

        WHERE id=?
        """,

        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        f'/edit-product/{id}'
    )

@app.route(
'/delete-product/<int:id>'
)
def delete_product(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        '/admin-products'
    )

@app.route(
    '/upload-image',
    methods=['GET', 'POST']
)
def upload_image():

    if request.method == 'POST':

        return "Image Uploaded"

    return render_template(
        'upload_image.html'
    )

@app.route(
'/gallery-upload',
methods=['GET','POST']
)
def gallery_upload():

    if "user_id" not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']

        image = request.files['image']

        filename = secure_filename(
            image.filename
        )

        image.save(
            os.path.join(
                'uploads/gallery',
                filename
            )
        )

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO gallery
            (
            title,
            filename
            )

            VALUES
            (?,?)
            """,
            (
                title,
                filename
            )
        )

        conn.commit()

        conn.close()

        return redirect('/gallery')

    return render_template(
        'gallery_upload.html'
    )

@app.route(
'/uploads/gallery/<filename>'
)
def gallery_file(filename):

    return send_from_directory(
        app.config[
            'GALLERY_UPLOAD_FOLDER'
        ],
        filename
    )

@app.route(
'/add-product-gallery/<int:product_id>',
methods=['GET','POST']
)
def add_product_gallery(product_id):
    if "user_id" not in session:
        return redirect('/login')

    if request.method == 'POST':

        image = request.files['image']

        filename = secure_filename(
            image.filename
        )

        image.save(
            os.path.join(
                app.config[
                    'PRODUCT_UPLOAD_FOLDER'
                ],
                filename
            )
        )

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO product_gallery
            (
            product_id,
            image
            )

            VALUES
            (
            ?, ?
            )
            """,

            (
                product_id,
                filename
            )
        )

        conn.commit()
        conn.close()

        return redirect(
            f'/manage-product-gallery/{product_id}'
        )

    return render_template(
        'add_product_gallery.html',
        product_id=product_id
    )

@app.route('/manage-product-gallery/<int:id>', methods=['GET', 'POST'])
def manage_product_gallery(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        image = request.files['image']

        if image:

            filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config['PRODUCT_UPLOAD_FOLDER'],
                    filename
                )
            )

            cursor.execute(
                """
                INSERT INTO product_gallery
                (
                    product_id,
                    image
                )
                VALUES (?,?)
                """,
                (id, filename)
            )

            conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM product_gallery
        WHERE product_id=?
        """,
        (id,)
    )

    gallery = cursor.fetchall()

    conn.close()

    return render_template(
        "manage_product_gallery.html",
        gallery=gallery,
        product_id=id
    )

@app.route('/delete-product-gallery/<int:id>')
def delete_product_gallery(id):

    conn = sqlite3.connect("industrial.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM product_gallery WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(request.referrer)

@app.route('/gallery')
def gallery():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM gallery_categories
        ORDER BY id DESC
    """)

    images = cursor.fetchall()

    conn.close()

    return render_template(
        "gallery.html",
        images=images
    )

@app.route('/manage-gallery-categories')
def manage_gallery_categories():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM gallery_categories
        """
    )

    images = cursor.fetchall()

    conn.close()

    return render_template(
        "manage_gallery_categories.html",
        images=images
    )

@app.route(
'/add-gallery-category',
methods=['GET', 'POST']
)
def add_gallery_category():

    if "user_id" not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']

        category = request.form['category']

        image = request.files['image']

        filename = secure_filename(
            image.filename
        )

        image.save(
            os.path.join(
                app.config[
                    'GALLERY_UPLOAD_FOLDER'
                ],
                filename
            )
        )

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO gallery_categories
            (
            title,
            image,
            category
            )

            VALUES
            (
            ?, ?, ?
            )
            """,
            (
                title,
                filename,
                category
            )
        )

        conn.commit()
        conn.close()

        return redirect(
            '/manage-gallery-categories'
        )

    return render_template(
        'add_gallery_category.html'
    )

@app.route('/machine-photos')
def machine_photos():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM gallery_categories
        WHERE category='Machine Photos'
        """
    )

    images = cursor.fetchall()

    conn.close()

    return render_template(
        'machine_photos.html',
        images=images
    )

@app.route('/installation-photos')
def installation_photos():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM gallery_categories
        WHERE category='Installation Photos'
        """
    )

    images = cursor.fetchall()

    conn.close()

    return render_template(
        'installation_photos.html',
        images=images
    )

@app.route(
'/edit-gallery-category/<int:id>',
methods=['GET', 'POST']
)
def edit_gallery_category(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM gallery_categories
        WHERE id=?
        """,
        (id,)
    )

    image = cursor.fetchone()

    if request.method == 'POST':

        title = request.form['title']
        category = request.form['category']

        new_image = request.files['image']

        filename = image['image']

        if new_image and new_image.filename != '':

            filename = secure_filename(
                new_image.filename
            )

            new_image.save(
                os.path.join(
                    app.config['GALLERY_UPLOAD_FOLDER'],
                    filename
                )
            )

        cursor.execute(
            """
            UPDATE gallery_categories

            SET
            title=?,
            image=?,
            category=?

            WHERE id=?
            """,
            (
                title,
                filename,
                category,
                id
            )
        )

        conn.commit()
        conn.close()

        return redirect(
            '/manage-gallery-categories'
        )

    conn.close()

    return render_template(
        'edit_gallery_category.html',
        image=image
    )

@app.route('/delete-gallery-category/<int:id>')
def delete_gallery_category(id):

    conn = sqlite3.connect("industrial.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM gallery_categories
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        '/manage-gallery-categories'
    )

@app.route(
'/delete-gallery/<int:id>'
)
def delete_gallery(id):
    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM gallery WHERE id=?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect('/gallery')

@app.route(
'/edit-gallery/<int:id>',
methods=['GET','POST']
)
def edit_gallery(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if request.method == 'POST':

        title = request.form['title']

        image = request.files['image']

        if image.filename:

            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config[
                        'GALLERY_UPLOAD_FOLDER'
                    ],
                    filename
                )
            )

            cursor.execute(
                """
                UPDATE gallery

                SET

                title=?,
                filename=?

                WHERE id=?
                """,

                (
                    title,
                    filename,
                    id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE gallery

                SET

                title=?

                WHERE id=?
                """,

                (
                    title,
                    id
                )
            )

        conn.commit()

        conn.close()

        return redirect(
            '/manage-gallery'
        )

    cursor.execute(
        "SELECT * FROM gallery WHERE id=?",
        (id,)
    )

    image = cursor.fetchone()

    conn.close()

    return render_template(
        'edit_gallery.html',
        image=image
    )

@app.route('/manage-gallery')
def manage_gallery():
    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM gallery"
    )

    images = cursor.fetchall()

    conn.close()

    return render_template(
        'manage_gallery.html',
        images=images
    )

@app.route('/admin-products')
def admin_products():

    if "user_id" not in session:
        return redirect('/login')

    search = request.args.get(
        'search',
        ''
    )

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE product_name
        LIKE ?
        """,
        (
            '%' + search + '%',
        )
    )

    products = cursor.fetchall()

    conn.close()

    return render_template(
        'admin_products.html',
        products=products
    )

@app.route(
'/inquiry/<product_name>',
methods=['GET','POST']
)
def inquiry(product_name):

    if request.method == 'POST':

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO inquiries
(
name,
email,
phone,
product,
message,
status
)

            VALUES
            (?, ?, ?, ?, ?, ?)
            """,

            (
                request.form['name'],
                request.form['email'],
                request.form['phone'],
                request.form['product'],
                request.form['message'],
                "Pending"
            )
        )

        conn.commit()

        conn.close()

        return redirect('/products')

    return render_template(
        'inquiry_form.html',
        product_name=product_name
    )

@app.route('/inquiries')
def inquiries():

    # STEP 1: Check Login
    if "user_id" not in session:
        return redirect("/login")

        # Admin + Manager only
    if session.get("role") not in ["Admin", "Manager"]:
        flash("Access Denied", "danger")
        return redirect("/dashboard")

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
                   SELECT id,
                          name,
                          email,
                          phone,
                          product,
                          message,
                          status,
                          created_at
                   FROM inquiries
                   ORDER BY id DESC
                   """)

    inquiries = cursor.fetchall()

    conn.close()

    return render_template(
        "inquiries.html",
        inquiries=inquiries
    )

@app.route("/customer-inquiry/<int:inquiry_id>")
def customer_inquiry_details(inquiry_id):

    # Login check
    if "user_id" not in session:
        return redirect("/login")

    # Admin + Manager only
    if session.get("role") not in ["Admin", "Manager"]:
        flash("Access Denied", "danger")
        return redirect("/dashboard")

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            product,
            message,
            status,
            created_at
        FROM inquiries
        WHERE id = ?
    """, (inquiry_id,))

    inquiry = cursor.fetchone()

    conn.close()

    if inquiry is None:
        flash("Inquiry not found.", "danger")
        return redirect("/inquiries")

    return render_template(
        "customer_inquiry_details.html",
        inquiry=inquiry
    )


@app.route(
'/delete-inquiry/<int:id>'
)
def delete_inquiry(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM inquiries
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        '/inquiries'
    )

@app.route(
'/approve-inquiry/<int:id>'
)
def approve_inquiry(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE inquiries

        SET status='Approved'

        WHERE id=?
        """,
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
        '/inquiries'
    )

@app.route('/featured-products')
def featured_products():

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM featured_products
        """
    )

    products = cursor.fetchall()

    conn.close()

    return render_template(
        'featured_products.html',
        products=products
    )

@app.route('/toggle-featured/<int:id>')
def toggle_featured(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM featured_products
        WHERE id=?
        """,
        (id,)
    )

    product = cursor.fetchone()

    if not product:
        conn.close()
        return "Featured Product Not Found"

    new_status = 0 if product['featured'] == 1 else 1

    cursor.execute(
        """
        UPDATE featured_products
        SET featured=?
        WHERE id=?
        """,
        (
            new_status,
            id
        )
    )

    conn.commit()
    conn.close()

    return redirect('/featured-products')

@app.route(
'/add-featured-product',
methods=['GET','POST']
)
def add_featured_product():

    if "user_id" not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']

        image = request.files['image']

        filename = secure_filename(
            image.filename
        )

        image.save(
            os.path.join(
                app.config[
                    'PRODUCT_UPLOAD_FOLDER'
                ],
                filename
            )
        )

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO featured_products
            (
            title,
            image
            )
            VALUES
            (
            ?, ?
            )
            """,
            (
                title,
                filename
            )
        )

        conn.commit()
        conn.close()

        return redirect(
            '/featured-products'
        )

    return render_template(
        'add_featured_product.html'
    )

@app.route(
'/manage-featured-products'
)
def manage_featured_products():

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM featured_products"
    )

    products = cursor.fetchall()

    conn.close()

    return render_template(
        'manage_featured_products.html',
        products=products
    )

@app.route(
'/delete-featured-product/<int:id>'
)
def delete_featured_product(id):

    conn = sqlite3.connect(
        "industrial.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM featured_products
        WHERE id=?
        """,
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        '/featured-products'
    )

@app.route(
'/edit-featured-product/<int:id>',
methods=['GET','POST']
)
def edit_featured_product(id):

    if "user_id" not in session:
        return redirect('/login')

    conn = sqlite3.connect(
        "industrial.db"
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if request.method == 'POST':

        title = request.form['title']

        image = request.files['image']

        if image.filename:

            filename = secure_filename(
                image.filename
            )

            image.save(
                os.path.join(
                    app.config[
                        'PRODUCT_UPLOAD_FOLDER'
                    ],
                    filename
                )
            )

            cursor.execute(
                """
                UPDATE featured_products

                SET

                title=?,
                image=?

                WHERE id=?
                """,

                (
                    title,
                    filename,
                    id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE featured_products

                SET

                title=?

                WHERE id=?
                """,

                (
                    title,
                    id
                )
            )

        conn.commit()

        conn.close()

        return redirect(
            '/featured-products'
        )

    cursor.execute(
        """
        SELECT * FROM featured_products
        WHERE id=?
        """,
        (id,)
    )

    product = cursor.fetchone()

    conn.close()

    return render_template(
        'edit_featured_product.html',
        product=product
    )

@app.route('/featured-product/<int:id>')
def featured_product_details(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Featured Product
    cursor.execute("""
        SELECT *
        FROM featured_products
        WHERE id=?
    """, (id,))
    featured = cursor.fetchone()

    if featured is None:
        conn.close()
        return "Featured Product Not Found"

    # Main Product by Title
    cursor.execute("""
    SELECT *
    FROM products
    WHERE product_name LIKE ?
    LIMIT 1
    """, ('%' + featured['title'] + '%',))

    product = cursor.fetchone()

    if product is None:
        conn.close()
        return f"Main Product '{featured['title']}' Not Found"

    cursor.execute("""
        SELECT *
        FROM product_gallery
        WHERE product_id=?
    """, (product["id"],))

    gallery = cursor.fetchall()

    conn.close()

    return render_template(
        "product_details.html",
        product=product,
        gallery=gallery
    )

@app.route('/turnkey')
def turnkey():

    return render_template(
        'turnkey.html'
    )


@app.route('/blog')
def blog():

    return render_template(
        'blog.html'
    )

@app.route('/admin/turnkey')
def admin_turnkey():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM turnkey_projects

    ORDER BY id DESC

    """)

    projects = cursor.fetchall()

    conn.close()

    return render_template(

        "admin_turnkey.html",

        projects=projects

    )

@app.route("/admin/price-requests")
def admin_price_requests():

    filter_type = request.args.get("filter", "all")

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if filter_type == "price":

        cursor.execute("""
        SELECT price_requests.*, products.image
        FROM price_requests
        LEFT JOIN products
        ON products.id = price_requests.product_id
        WHERE request_type='price'
        ORDER BY price_requests.id DESC
        """)

    elif filter_type == "quotation":

        cursor.execute("""
        SELECT price_requests.*, products.image
        FROM price_requests
        LEFT JOIN products
        ON products.id = price_requests.product_id
        WHERE request_type='quotation'
        ORDER BY price_requests.id DESC
        """)

    elif filter_type == "pending":

        cursor.execute("""
        SELECT price_requests.*, products.image
        FROM price_requests
        LEFT JOIN products
        ON products.id = price_requests.product_id
        WHERE status='New'
        ORDER BY price_requests.id DESC
        """)

    elif filter_type == "completed":

        cursor.execute("""
        SELECT price_requests.*, products.image
        FROM price_requests
        LEFT JOIN products
        ON products.id = price_requests.product_id
        WHERE status='Completed'
        ORDER BY price_requests.id DESC
        """)

    else:

        cursor.execute("""
        SELECT price_requests.*, products.image
        FROM price_requests
        LEFT JOIN products
        ON products.id = price_requests.product_id
        ORDER BY price_requests.id DESC
        """)

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "price_requests.html",
        requests=requests,
        filter_type=filter_type
    )

@app.route("/thank-you")
def thank_you():

    return render_template("thank_you.html")

@app.route("/price-request-reply/<int:id>", methods=["GET","POST"])
def price_request_reply(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM price_requests WHERE id=?",

        (id,)

    )

    request_data = cursor.fetchone()

    if request.method == "POST":

        reply = request.form["reply"]

        status = request.form["status"]

        quotation = request.files["quotation"]

        filename = ""

        if quotation.filename != "":

            filename = secure_filename(

                quotation.filename

            )

            quotation.save(

                os.path.join(

                    "static/quotations",

                    filename

                )

            )

        cursor.execute("""

        UPDATE price_requests

        SET

        reply_message=?,

        quotation_file=?,

        status=?

        WHERE id=?

        """,

        (

            reply,

            filename,

            status,

            id

        ))

        conn.commit()

        conn.close()

        return redirect("/admin/price-requests")

    conn.close()

    return render_template(

        "reply_quotation.html",

        request_data=request_data

    )

@app.route("/quotation-request/<int:id>", methods=["GET", "POST"])
def quotation_request(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (id,)
    )

    product = cursor.fetchone()

    request_type = request.args.get("type", "quotation")

    if product is None:
        conn.close()
        return "Product Not Found"

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        company = request.form["company"]
        email = request.form["email"]
        phone = request.form["phone"]
        city = request.form["city"]
        quantity = request.form["quantity"]
        message = request.form["message"]

        cursor.execute("""
            INSERT INTO price_requests(
                product_id,
                product_name,
                customer_name,
                company_name,
                email,
                phone,
                city,
                quantity,
                message,
                request_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product["id"],
            product["product_name"],
            customer_name,
            company,
            email,
            phone,
            city,
            quantity,
            message,
            request_type
        ))

        conn.commit()
        conn.close()

        return redirect("/thank-you")

    conn.close()

    return render_template(
        "quotation_request.html",
        product=product,
        request_type=request_type
    )

@app.route("/price-request-view/<int:id>")
def price_request_view(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        price_requests.*,
        products.image
    FROM price_requests
    LEFT JOIN products
    ON products.id = price_requests.product_id
    WHERE price_requests.id=?
    """, (id,))

    request_data = cursor.fetchone()

    conn.close()

    return render_template(
        "price_request_view.html",
        request_data=request_data
    )

@app.route("/update-request-status/<int:id>/<status>")
def update_request_status(id, status):

    conn = sqlite3.connect("industrial.db")

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE price_requests

    SET status=?

    WHERE id=?

    """,(status,id))

    conn.commit()

    conn.close()

    return redirect("/admin/price-requests")

@app.route("/delete-price-request/<int:id>")
def delete_price_request(id):

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM price_requests WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Request deleted successfully.", "success")

    return redirect("/admin/price-requests")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    error = None

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()

        conn = sqlite3.connect("industrial.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE LOWER(username)=?
        AND LOWER(email)=?
        """, (username.lower(), email))

        user = cursor.fetchone()

        if user:

            otp = save_otp(email)

            conn.close()

            # Email મોકલો
            if not send_otp(email, otp):
                flash("OTP email could not be sent.", "danger")
                return redirect("/forgot-password")

            session["reset_email"] = email

            flash("OTP has been sent to your email.", "success")

            return redirect("/reset-otp")

        conn.close()

        error = "Invalid Username or Email."

    return render_template("forgot_password.html", error=error)


@app.route("/reset-otp", methods=["GET", "POST"])
def reset_otp():

    if "reset_email" not in session:
        return redirect("/forgot-password")

    error = None

    if request.method == "POST":

        otp = request.form["otp"].strip()

        conn = sqlite3.connect("industrial.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM otp_verification
        WHERE email=? AND otp=?
        """, (session["reset_email"], otp))

        record = cursor.fetchone()

        conn.close()

        if record:

            return redirect("/new-password")

        else:

            error = "Invalid OTP."

    return render_template(
        "reset_otp.html",
        error=error
    )


@app.route("/new-password", methods=["GET", "POST"])
def new_password():

    if "reset_email" not in session:
        return redirect("/forgot-password")

    error = None

    if request.method == "POST":

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            error = "Passwords do not match."

        else:

            password_hash = generate_password_hash(password)

            conn = sqlite3.connect("industrial.db")
            cursor = conn.cursor()

            cursor.execute("""
            UPDATE users
            SET password=?
            WHERE email=?
            """, (password_hash, session["reset_email"]))

            cursor.execute("""
            DELETE FROM otp_verification
            WHERE email=?
            """, (session["reset_email"],))

            conn.commit()
            conn.close()

            session.pop("reset_email", None)

            flash("Password changed successfully. Please login.", "success")

            return redirect("/login")

    return render_template(
        "new_password.html",
        error=error
    )


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_user" not in session:

        return redirect("/forgot-password")

    if request.method == "POST":

        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:

            flash("Passwords do not match.", "danger")

        else:

            password_hash = generate_password_hash(new_password)

            conn = sqlite3.connect("industrial.db")
            cursor = conn.cursor()

            cursor.execute("""
                           UPDATE users
                           SET password=?
                           WHERE username = ?
                           """, (
                               password_hash,
                               session["reset_user"]
                           )
                           )

            conn.commit()
            conn.close()

            session.pop("reset_user")

            flash(
                "Password changed successfully. Please login.",
                "success"
            )

            return redirect("/login")

    return render_template("reset_password.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Load Department List
    cursor.execute("""
        SELECT id, department_name
        FROM departments
        ORDER BY department_name
    """)
    departments = cursor.fetchall()

    # Load Role List
    cursor.execute("""
        SELECT id, role_name
        FROM roles
        ORDER BY role_name
    """)
    roles = cursor.fetchall()

    if request.method == "POST":


        full_name = request.form.get("full_name", "").strip()
       # print("STEP 2 : Form Data Loaded")
        username = request.form["username"].strip()

        email = request.form["email"].strip().lower()

        if session.get("email_verified") != True:
            flash("Please verify your Email first.", "danger")

            conn.close()

            return render_template(
                "register.html",
                departments=departments,
                roles=roles
            )

        if session.get("verified_email") != email:
            flash("Email verification failed.", "danger")

            conn.close()

            return render_template(
                "register.html",
                departments=departments,
                roles=roles
            )

        mobile = request.form["mobile"].strip()

        department_id = request.form["department_id"]
        cursor.execute("""
                       SELECT id
                       FROM roles
                       WHERE role_name = ?
                       """, ("Manager",))

        role = cursor.fetchone()

        if role is None:
            conn.close()
            return "Manager role not found"

        role_id = role["id"]

        #  print("STEP 3 : Password Check")

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Password Match
        if password != confirm_password:

            flash("Passwords do not match.", "danger")

            conn.close()

            return render_template(
                "register.html",
                departments=departments,
                roles=roles
            )

        #   print("STEP 4 : Password OK")

        # Username Exists?
        # Username Exists?
        cursor.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

      #  print("Username Check :", user)

        if user:
            flash("Username already exists.", "danger")

            conn.close()

            return render_template(
                "register.html",
                departments=departments,
                roles=roles
            )

        #   print("STEP 5 : Username OK")

        # Email Exists?
        cursor.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        )

        mail = cursor.fetchone()

     #   print("Email Check :", mail)

        if mail:
            flash("Email already registered.", "danger")

            conn.close()

            return render_template(
                "register.html",
                departments=departments,
                roles=roles
            )

        #   print("STEP 6 : Email OK")

        password_hash = generate_password_hash(password)

        #  print("STEP 7 : About to Insert User")

        cursor.execute("""
        INSERT INTO users
        (
            full_name,
            username,
            email,
            mobile,
            password,
            department_id,
            role_id,
            account_status,
            is_verified,
            email_verified
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
                       (
                           full_name,
                           username,
                           email,
                           mobile,
                           password_hash,
                           department_id,
                           role_id,
                           "Pending",
                           1,
                           1
                       ))

        conn.commit()

        print("✅ User Saved Successfully :", username)

        #   print("STEP 9 : Sending OTP")

        conn.close()

        session.pop("email_verified", None)
        session.pop("verified_email", None)

        flash(
            "Account Created Successfully.",
            "success"
        )

        return redirect("/login")

    conn.close()

    return render_template(
        "register.html",
        departments=departments,
        roles=roles
    )

@app.route("/manage-users")
def manage_users():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect("/dashboard")

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""

    SELECT

        users.*,
        departments.department_name,
        roles.role_name

    FROM users

    LEFT JOIN departments
    ON users.department_id = departments.id

    LEFT JOIN roles
    ON users.role_id = roles.id

    ORDER BY users.id DESC

    """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "manage_users.html",
        users=users
    )

@app.route("/approve-user/<int:id>")
def approve_user(id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return redirect("/dashboard")

    conn = sqlite3.connect("industrial.db")
    cursor = conn.cursor()

    cursor.execute("""

        UPDATE users

        SET account_status='Active'

        WHERE id=?

    """,(id,))

    conn.commit()

    conn.close()

    flash("User Approved Successfully.","success")

    return redirect("/manage-users")

@app.route("/delete-user/<int:id>")
def delete_user(id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return redirect("/dashboard")

    conn = sqlite3.connect("industrial.db")
    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM users WHERE id=?",

        (id,)

    )

    conn.commit()

    conn.close()

    flash("User Deleted.","success")

    return redirect("/manage-users")

from werkzeug.security import generate_password_hash

@app.route("/reset-admin")
def reset_admin():

    conn = sqlite3.connect("industrial.db")
    cursor = conn.cursor()

    password_hash = generate_password_hash("123456")

    cursor.execute("""
    UPDATE users
    SET password=?
    WHERE username='admin'
    """, (password_hash,))

    conn.commit()
    conn.close()

    return "Admin Password Reset Successfully"

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if "verify_email" not in session:
        return redirect("/register")

    email = session["verify_email"]

    if request.method == "POST":

        otp = request.form["otp"].strip()

        conn = sqlite3.connect("industrial.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM otp_verification
        WHERE email=? AND otp=?
        """, (email, otp))

        record = cursor.fetchone()

        if record:

            # User Verify
            cursor.execute("""
            UPDATE users
            SET is_verified=1
            WHERE email=?
            """, (email,))

            print("=" * 40)
            print("User Verified Successfully")
            print("Email :", email)
            print("=" * 40)

            # OTP Delete
            cursor.execute("""
            DELETE FROM otp_verification
            WHERE email=?
            """, (email,))

            conn.commit()
            conn.close()

            session.pop("verify_email")

            flash(
                "Email Verified Successfully. Please wait for Admin Approval.",
                "success"
            )

            return redirect("/login")

        conn.close()

        flash("Invalid OTP.", "danger")

    return render_template("verify_otp.html")

@app.route("/verify-email-otp", methods=["POST"])
def verify_email_otp():

    email = request.form["email"].strip().lower()
    otp = request.form["otp"].strip()

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM otp_verification
        WHERE email=?
        AND otp=?
        AND verified=0
    """,(email, otp))

    record = cursor.fetchone()

    if record is None:

        cursor.execute("""
                       SELECT *
                       FROM otp_verification
                       WHERE email = ?
                       """, (email,))

        data = cursor.fetchone()

        if data:

            attempts = data["attempts"] + 1

            cursor.execute("""
                           UPDATE otp_verification
                           SET attempts=?
                           WHERE email = ?
                           """,
                           (
                               attempts,
                               email
                           ))

            conn.commit()

            if attempts >= 3:
                cursor.execute("""
                               DELETE
                               FROM otp_verification
                               WHERE email = ?
                               """, (email,))

                conn.commit()

                conn.close()

                return jsonify({

                    "status": "error",

                    "message": "Maximum attempts reached. Please resend OTP."

                })

        conn.close()

        return jsonify({

            "status": "error",

            "message":"Invalid OTP"

        })


    cursor.execute("""
        UPDATE otp_verification
        SET verified=1
        WHERE email=?
    """, (email,))

    cursor.execute("""
                   UPDATE users
                   SET is_verified    = 1,
                       email_verified = 1
                   WHERE email = ?
                   """, (email,))

    cursor.execute("""
                   DELETE
                   FROM otp_verification
                   WHERE email = ?
                   """, (email,))

    conn.commit()

    session["email_verified"] = True
    session["verified_email"] = email

    conn.close()

    return jsonify({
        "status":"success"
    })

@app.route("/resend-email-otp", methods=["POST"])
def resend_email_otp():

    email = request.form["email"].strip().lower()

    otp = save_otp(email)

    if send_otp(email, otp):

        return jsonify({

            "status":"success"

        })

    return jsonify({

        "status":"error"

    })

@app.route("/resend-otp")
def resend_otp():

    if "verify_email" not in session:
        return redirect("/register")

    email = session["verify_email"]

    otp = str(random.randint(100000,999999))

    conn = sqlite3.connect("industrial.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM otp_verification
        WHERE email=?
    """,(email,))

    cursor.execute("""
        INSERT INTO otp_verification
        (
            email,
            otp
        )
        VALUES
        (
            ?,?
        )
    """,(email,otp))

    conn.commit()
    conn.close()

    send_otp(email,otp)

    flash("New OTP sent successfully.","success")

    return redirect("/verify-otp")

@app.route("/price-requests")
def price_requests():

    # STEP 1: Login Check
    if "user_id" not in session:

        return redirect("/login")


    # STEP 2: Admin + Manager Only
    if session.get("role") not in ["Admin", "Manager"]:

        flash("Access Denied", "danger")

        return redirect("/dashboard")


    # STEP 3: Database Connection
    conn = sqlite3.connect("industrial.db")

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    # STEP 4: Get Price Requests
    cursor.execute("""
        SELECT
            id,
            product_id,
            product_name,
            customer_name,
            company_name,
            email,
            phone,
            city,
            quantity,
            message,
            created_at,
            status,
            reply_message,
            quotation_file,
            request_type
        FROM price_requests
        ORDER BY id DESC
    """)

    requests = cursor.fetchall()


    # STEP 5: Close Database
    conn.close()


    # STEP 6: Open Page
    return render_template(
        "price_requests.html",
        requests=requests
    )

# =========================================
# CATALOG ACCESS FORM
# =========================================

@app.route('/catalog-access', methods=['GET', 'POST'])
def catalog_access():

    if request.method == 'POST':

        name = request.form.get(
            'name', ''
        ).strip()

        company = request.form.get(
            'company', ''
        ).strip()

        email = request.form.get(
            'email', ''
        ).strip()

        phone = request.form.get(
            'phone', ''
        ).strip()

        city = request.form.get(
            'city', ''
        ).strip()


        # ---------------------------------
        # VALIDATION
        # ---------------------------------

        if not name or not email or not phone:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for('catalog_access')
            )


        # ---------------------------------
        # DATABASE
        # ---------------------------------

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()


        # ---------------------------------
        # CREATE CATALOG LEADS TABLE
        # ---------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalog_leads (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                company TEXT,

                email TEXT NOT NULL,

                phone TEXT NOT NULL,

                city TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                opened_at TEXT

            )
        """)


        # ---------------------------------
        # ADD opened_at IF OLD TABLE EXISTS
        # ---------------------------------

        cursor.execute(
            "PRAGMA table_info(catalog_leads)"
        )

        columns = [
            row[1]
            for row in cursor.fetchall()
        ]


        if 'opened_at' not in columns:

            cursor.execute("""
                ALTER TABLE catalog_leads
                ADD COLUMN opened_at TEXT
            """)


        # ---------------------------------
        # SAVE LEAD
        # ---------------------------------

        cursor.execute("""
            INSERT INTO catalog_leads
            (
                name,
                company,
                email,
                phone,
                city
            )
            VALUES (?, ?, ?, ?, ?)
        """, (

            name,
            company,
            email,
            phone,
            city

        ))


        lead_id = cursor.lastrowid


        conn.commit()
        conn.close()


        # ---------------------------------
        # SAVE LEAD ID IN SESSION
        # ---------------------------------

        session['catalog_access'] = True

        session['catalog_lead_id'] = lead_id


        return redirect(
            url_for('catalog_view')
        )


    return render_template(
        'catalog_access.html'
    )

# =========================================
# PROTECTED CATALOG VIEW
# =========================================

@app.route('/catalog-view')
def catalog_view():

    if not session.get('catalog_access'):
        return redirect('/catalog-access')

    return render_template(
        'catalog_view.html'
    )

# =========================================
# PROTECTED CATALOG PDF
# =========================================

@app.route('/catalog-pdf')
def catalog_pdf():

    # -------------------------------------
    # SECURITY
    # -------------------------------------

    if not session.get('catalog_access'):

        return redirect(
            url_for('catalog_access')
        )


    # -------------------------------------
    # MARK CATALOG AS OPENED
    # -------------------------------------

    lead_id = session.get(
        'catalog_lead_id'
    )


    if lead_id:

        conn = sqlite3.connect(
            "industrial.db"
        )

        cursor = conn.cursor()


        # Only mark first opening.
        # This prevents iframe + button
        # from creating multiple opens.

        cursor.execute("""
            UPDATE catalog_leads

            SET opened_at = CURRENT_TIMESTAMP

            WHERE id = ?

            AND opened_at IS NULL
        """, (
            lead_id,
        ))


        conn.commit()
        conn.close()


    # -------------------------------------
    # SERVE ORIGINAL PDF
    # -------------------------------------

    return send_from_directory(

        app.static_folder,

        'catalog.pdf',

        mimetype='application/pdf',

        as_attachment=False

    )

# =========================================
# ADMIN - CATALOG LEADS
# =========================================

@app.route('/catalog-leads')
def catalog_leads():

    # -------------------------------------
    # ADMIN SECURITY
    # -------------------------------------

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        flash("Access Denied.", "danger")
        return redirect("/dashboard")


    # -------------------------------------
    # DATABASE
    # -------------------------------------

    conn = sqlite3.connect("industrial.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    # -------------------------------------
    # MAKE SURE TABLE EXISTS
    # -------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalog_leads (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            company TEXT,

            email TEXT NOT NULL,

            phone TEXT NOT NULL,

            city TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            opened_at TEXT

        )
    """)


    # -------------------------------------
    # GET ALL CATALOG VISITORS
    # -------------------------------------

    cursor.execute("""
        SELECT *
        FROM catalog_leads
        ORDER BY id DESC
    """)

    catalog_leads = cursor.fetchall()


    # -------------------------------------
    # TOTAL CATALOG OPENS
    # -------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM catalog_leads
        WHERE opened_at IS NOT NULL
    """)

    catalog_opens = cursor.fetchone()[0]


    conn.close()


    # -------------------------------------
    # SEND DATA TO TEMPLATE
    # -------------------------------------

    return render_template(
        "catalog_leads.html",

        # IMPORTANT
        # Template uses: {% for lead in leads %}
        leads=catalog_leads,

        catalog_opens=catalog_opens
    )

# ==========================================
# CUSTOMER SIGNUP
# ==========================================

@app.route("/signup", methods=["POST"])
def signup():
    import re

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip().lower()
    terms = request.form.get("terms")

    # Server-side validation
    if not full_name or not phone or not email or terms != "accepted":
        return redirect(url_for("home", signup_status="invalid"))

    if len(full_name) > 100:
        return redirect(url_for("home", signup_status="invalid_name"))

    # Accept 10-digit Indian mobile numbers, optionally with +91
    if not re.fullmatch(r"(?:\+91[\s-]?)?[6-9]\d{9}", phone):
        return redirect(url_for("home", signup_status="invalid_phone"))

    if len(email) > 254 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        return redirect(url_for("home", signup_status="invalid_email"))

    conn = sqlite3.connect(
        os.path.join(BASE_DIR, "industrial.db")
    )
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                terms_accepted INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            INSERT INTO customer_signups
                (full_name, phone, email, terms_accepted)
            VALUES (?, ?, ?, 1)
        """, (full_name, phone, email))

        conn.commit()

    except sqlite3.IntegrityError:
        return redirect(url_for("home", signup_status="duplicate_email"))

    except sqlite3.Error:
        app.logger.exception("Customer signup database error")
        return redirect(url_for("home", signup_status="error"))

    finally:
        conn.close()

    return redirect(url_for("home", signup_status="success"))

# ==========================================
# ADMIN: CUSTOMER SIGNUPS
# ==========================================

@app.route("/customer-signups")
def customer_signups():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        flash("Access Denied", "danger")
        return redirect("/dashboard")

    conn = sqlite3.connect(
        os.path.join(BASE_DIR, "industrial.db")
    )
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                terms_accepted INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        signups = conn.execute("""
            SELECT id, full_name, phone, email, created_at
            FROM customer_signups
            ORDER BY id DESC
        """).fetchall()

    finally:
        conn.close()

    return render_template(
        "customer_signups.html",
        signups=signups
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )