"""Per-kind building blocks for the app spec. Pure data.

Field token:  name:type[!][@]   ! = required, @ = unique.
Types: string text int float bool datetime email url ref(Entity) enum(a|b|c)
Entity access: read / write in {public, user, owner, admin}. 'owner' = the record's creator (or admin).
"""

KIND_LABEL = {"portfolio": "Portfolio website", "landing": "Marketing landing page", "site": "Informational website",
              "dashboard": "Dashboard application", "ecommerce": "E-commerce application", "chat": "Real-time chat application",
              "chatbot": "AI chat assistant", "management": "Management system", "cms": "Content platform",
              "social": "Social / community platform", "local": "Local single-user application", "generic": "Website"}

USERS = {"portfolio": "Recruiters, clients and collaborators evaluating the owner's work",
         "landing": "Prospective customers deciding whether to try the product",
         "site": "Visitors looking for information and a way to get in touch",
         "dashboard": "Team members and admins who monitor and act on data",
         "ecommerce": "Shoppers (customers) and store administrators",
         "chat": "Registered users talking to each other in rooms or direct messages",
         "chatbot": "End users asking questions and getting AI answers",
         "management": "Staff who manage records and the people those records describe",
         "cms": "Editors who publish and readers who consume content",
         "social": "Members who post, follow and interact",
         "local": "A single person using the tool on their own device",
         "generic": "General visitors"}

ROLES = {"ecommerce": ["customer", "admin"], "management": ["admin", "staff", "viewer"], "cms": ["reader", "editor", "admin"],
         "social": ["member", "admin"], "chat": ["member", "admin"], "dashboard": ["member", "admin"]}

# (slug, title, needs_login)
PAGES = {
    "portfolio": [("home", "Home", 0), ("work", "Work", 0), ("about", "About", 0), ("contact", "Contact", 0)],
    "landing": [("home", "Home", 0)],
    "site": [("home", "Home", 0), ("about", "About", 0), ("services", "Programs & Services", 0), ("gallery", "Gallery", 0), ("contact", "Contact", 0)],
    "dashboard": [("overview", "Overview", 1), ("analytics", "Analytics", 1), ("records", "Records", 1), ("settings", "Settings", 1)],
    "ecommerce": [("home", "Home", 0), ("catalog", "Catalog", 0), ("category", "Category", 0),
                  ("product", "Product detail", 0), ("cart", "Cart", 0), ("wishlist", "Wishlist", 1),
                  ("checkout", "Checkout", 1), ("addresses", "Address book", 1), ("orders", "My orders", 1),
                  ("profile", "Profile", 1), ("admin", "Admin overview", 1),
                  ("admin-products", "Admin products and inventory", 1), ("admin-orders", "Admin order management", 1)],
    "chat": [("chat", "Chat", 1), ("profile", "Profile", 1)],
    "chatbot": [("chat", "Chat", 0), ("history", "History", 1), ("settings", "Settings", 0)],
    "management": [("dashboard", "Dashboard", 1), ("records", "Records", 1), ("detail", "Record detail", 1), ("reports", "Reports", 1), ("settings", "Settings", 1)],
    "cms": [("home", "Home", 0), ("article", "Article", 0), ("category", "Category", 0), ("editor", "Editor", 1), ("admin", "Admin", 1)],
    "social": [("feed", "Feed", 1), ("profile", "Profile", 0), ("post", "Post", 0), ("notifications", "Notifications", 1)],
    "local": [("main", "Main", 0)],
    "generic": [("home", "Home", 0), ("about", "About", 0), ("contact", "Contact", 0)],
}
LOGIN_PAGES = [("login", "Sign in", 0), ("register", "Create account", 0)]

FEATURES = {
    "portfolio": ["Project showcase with filtering", "About and skills", "Working contact form"],
    "landing": ["Hero with primary call to action", "Feature highlights", "Social proof", "Pricing / sign-up call to action"],
    "site": ["Programs or services overview", "Photo gallery", "Enquiry / contact form", "Location and contact details"],
    "dashboard": ["KPI summary cards", "Interactive charts", "Searchable, sortable, paginated data table", "Light / dark theme"],
    "ecommerce": [
        "Product catalog with search, category filters, sorting and cursor pagination",
        "Product detail page with image gallery, stock-aware quantity and related products",
        "Persistent cart with quantity validation and checkout-time price/stock revalidation",
        "Account-scoped wishlist and address book",
        "Checkout shared by Buy Now and cart flows, with honest payment status",
        "Order history with immutable purchase snapshots and status timeline",
        "Admin product/category management, inventory and validated image uploads",
        "Admin order queue with authorized status transitions and audit trail",
        "Loading, empty, error, retry, validation and success states across critical flows",
    ],
    "chat": ["Rooms and direct messages", "Live message delivery", "Message history with pagination", "Unread indicators"],
    "chatbot": ["Streaming AI answers", "Conversation history", "Clear loading, error and empty states"],
    "management": ["Record list with search, filter and pagination", "Create / edit / delete records with validation", "Role-based access", "Reports and summaries"],
    "cms": ["Article editor", "Categories and tags", "Draft / published workflow", "Public article pages with SEO metadata"],
    "social": ["Post feed with pagination", "Comments and likes", "Follow / unfollow", "Profile pages"],
    "local": ["Create, edit and delete items", "Data stays on the device"],
    "generic": ["Content pages", "Responsive navigation"],
}

# Entity templates. Each: name -> (fields, read, write)
USER = (["email:email!@", "name:string!", "password_hash:string!", "role:enum({roles})!", "created_at:datetime!"], "admin", "owner")
ENTITIES = {
    "portfolio": {"Project": (["title:string!", "summary:text!", "url:url", "image_url:url", "tags:string", "sort_order:int"], "public", "admin")},
    "landing": {},
    "site": {},
    "dashboard": {"Record": (["title:string!", "status:enum(open|in_progress|done)!", "value:float", "category:string", "owner_id:ref(User)"], "user", "owner")},
    "ecommerce": {
        "Category": (["name:string!@", "slug:string!@", "active:bool!", "sort_order:int"], "public", "admin"),
        "Product": (["name:string!", "description:text", "brand:string", "sku:string", "price:float!", "stock:int!", "image_url:url", "category_id:ref(Category)", "active:bool!", "created_at:datetime!"], "public", "admin"),
        "CartItem": (["user_id:ref(User)", "product_id:ref(Product)!", "quantity:int!", "created_at:datetime"], "owner", "owner"),
        "WishlistItem": (["user_id:ref(User)", "product_id:ref(Product)!", "created_at:datetime"], "owner", "owner"),
        "Address": (["user_id:ref(User)", "full_name:string!", "phone:string!", "address_line1:string!", "address_line2:string", "city:string!", "state:string!", "postal_code:string!", "country:string!", "is_default:bool", "created_at:datetime"], "owner", "owner"),
        # Generic CRUD must not let a customer edit price, owner, payment state or order status.
        # Checkout creates customer orders through the dedicated server-side workflow; admin handles state changes.
        "Order": (["user_id:ref(User)!", "status:enum(pending|paid|confirmed|packed|shipped|delivered|cancelled)!", "total:float!", "created_at:datetime!"], "owner", "admin"),
        "OrderItem": (["order_id:ref(Order)!", "product_id:ref(Product)!", "user_id:ref(User)!", "product_name:string!", "quantity:int!", "unit_price:float!", "line_total:float!"], "owner", "owner")},
    "chat": {"Room": (["name:string!", "is_direct:bool!"], "user", "user"),
             "Message": (["room_id:ref(Room)!", "sender_id:ref(User)!", "body:text!", "created_at:datetime!"], "user", "owner")},
    "chatbot": {"Conversation": (["user_id:ref(User)", "title:string", "created_at:datetime!"], "owner", "owner"),
                "ChatMessage": (["conversation_id:ref(Conversation)!", "role:enum(user|assistant)!", "content:text!", "created_at:datetime!"], "owner", "owner")},
    "management": {"Department": (["name:string!@"], "user", "admin"),
                   "Record": (["title:string!", "department_id:ref(Department)", "status:enum(active|inactive)!", "notes:text", "created_at:datetime!"], "user", "user")},
    "cms": {"Category": (["name:string!@", "slug:string!@"], "public", "admin"),
            "Post": (["title:string!", "slug:string!@", "body:text!", "status:enum(draft|published)!", "category_id:ref(Category)", "author_id:ref(User)!", "published_at:datetime"], "public", "owner")},
    "social": {"Post": (["author_id:ref(User)!", "body:text!", "created_at:datetime!"], "user", "owner"),
               "Comment": (["post_id:ref(Post)!", "author_id:ref(User)!", "body:text!", "created_at:datetime!"], "user", "owner"),
               "Follow": (["follower_id:ref(User)!", "followee_id:ref(User)!"], "user", "owner")},
    "local": {"Item": (["title:string!", "done:bool!", "notes:text", "created_at:datetime!"], "public", "public")},
    "generic": {},
}
# Domain variants for kind 'management' (regex on the brief) -> replaces the generic Department/Record pair.
MANAGEMENT_VARIANTS = [
    (r"college|school|university|student|attendance|admission|\blms\b|course", "education", {
        "Department": (["name:string!@"], "user", "admin"),
        "Course": (["code:string!@", "title:string!", "department_id:ref(Department)", "credits:int"], "user", "admin"),
        "Student": (["roll_no:string!@", "name:string!", "email:email", "department_id:ref(Department)", "year:int"], "user", "staff"),
        "Enrollment": (["student_id:ref(Student)!", "course_id:ref(Course)!", "grade:string"], "user", "staff"),
        "Attendance": (["student_id:ref(Student)!", "course_id:ref(Course)!", "date:datetime!", "present:bool!"], "user", "staff")}),
    (r"hospital|clinic|patient|doctor|appointment", "healthcare", {
        "Patient": (["name:string!", "dob:datetime", "phone:string", "email:email"], "staff", "staff"),
        "Doctor": (["name:string!", "speciality:string"], "user", "admin"),
        "Appointment": (["patient_id:ref(Patient)!", "doctor_id:ref(Doctor)!", "scheduled_at:datetime!", "status:enum(booked|done|cancelled)!"], "staff", "staff")}),
    (r"inventory|stock|warehouse|supplier", "inventory", {
        "Supplier": (["name:string!", "contact:string"], "user", "staff"),
        "Item": (["sku:string!@", "name:string!", "quantity:int!", "supplier_id:ref(Supplier)"], "user", "staff"),
        "StockMovement": (["item_id:ref(Item)!", "delta:int!", "reason:string", "created_at:datetime!"], "user", "staff")}),
]

# Extra entities pulled in by needs.
NEED_ENTITIES = {
    "payments": {"Payment": (["user_id:ref(User)", "order_ref:string!", "provider:string!", "provider_ref:string!@", "amount:float!", "status:enum(pending|succeeded|failed)!", "created_at:datetime!"], "owner", "admin")},
    "uploads": {"FileAsset": (["owner_id:ref(User)", "filename:string!", "mime_type:string!", "size_bytes:int!", "storage_key:string!@"], "owner", "owner")},
    "newsletter": {"Subscriber": (["email:email!@", "created_at:datetime!"], "admin", "public")},
    "contact": {"Enquiry": (["name:string!", "email:email!", "message:text!", "created_at:datetime!"], "admin", "public")},
}
