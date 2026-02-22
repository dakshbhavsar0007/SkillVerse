import os
from groq import Groq
from flask import current_app
import logging
import traceback

class ChatManager:
    def __init__(self):
        self.model = None
        self._setup_done = False
        self._init_error = None

    def setup(self):
        api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            self._init_error = "GROQ_API_KEY missing from config and environment"
            logging.error(f"AskVera: {self._init_error}")
            return

        logging.info(f"AskVera: Attempting init with key starting '{api_key[:8]}...'")
        
        try:
            self.model = Groq(api_key=api_key)
            self._setup_done = True
            self._init_error = None
            logging.info("AskVera: Groq AI initialized successfully.")
        except Exception as e:
            self._init_error = str(e)
            logging.error(f"AskVera init failed: {e}")
            traceback.print_exc()

    def get_response(self, user_message, context, user_identity, user_role="guest"):
        if not current_app.config.get("ENABLE_ASKVERA", False):
            return {"error": "AskVera is disabled.", "fallback": True}

        if not self.model: 
            self.setup()
        
        if not self.model: 
            err_detail = self._init_error or "Unknown error"
            logging.error(f"AskVera: Model still None after setup. Error: {err_detail}")
            return {"error": f"AI service unavailable ({err_detail}).", "fallback": True}

        try:
            system_prompt = (
                "You are AskVera, the official AI assistant of SkillVerse — a freelance marketplace platform "
                "that connects skilled professionals (providers) with clients (customers) for paid services.\n\n"

                "=== PLATFORM OVERVIEW ===\n"
                "SkillVerse is a service marketplace where:\n"
                "- Providers list their skills/services (e.g. Web Development, Graphic Design, Video Editing, Tutoring, Marketing, Music & Audio, Photography, Content Writing)\n"
                "- Customers browse, search, and place orders for those services\n"
                "- Payments are in Indian Rupees (₹)\n"
                "- Platform URL: https://skillverse-oh9z.onrender.com\n\n"

                "=== USER ROLES ===\n"
                f"Current user role: {user_role}\n"
                "- guest: Not logged in. Can browse services, must register to order.\n"
                "- customer/client: Can browse, search, place orders, book sessions, leave reviews, track orders, download completion certificates.\n"
                "- provider/seller: Can create & manage service listings, accept/reject orders, manage availability slots, mark orders complete, view earnings.\n"
                "- admin: Can manage all users, approve/reject skill submissions, manage categories, view platform-wide orders and activity.\n\n"

                "=== KEY FEATURES ===\n"
                "1. SERVICES: Providers create listings with title, description, price (₹), delivery time, category, and images. "
                "Admin must approve listings before they go live. Rejected listings show a reason and can be edited & resubmitted.\n\n"
                "2. ORDERS: Customer places order → Provider accepts/rejects → Work happens → Provider marks complete → "
                "Customer gets completion certificate + can leave a review. Order statuses: Pending, In Progress, Completed, Cancelled.\n\n"
                "3. BOOKINGS & AVAILABILITY: Providers set available time slots. Customers can book a specific slot. "
                "Provider can confirm or reject booking requests. Confirmed bookings send email notifications.\n\n"
                "4. REAL-TIME CHAT: Each order has a built-in chat so customer and provider can communicate directly.\n\n"
                "5. REVIEWS & RATINGS: After order completion, customers can leave a star rating and review on the service page.\n\n"
                "6. CERTIFICATES: On order completion, customers receive a downloadable certificate of completion with a unique cert ID.\n\n"
                "7. CATEGORIES: Web Development, Graphic Design, Content Writing, Video Editing, Tutoring, Music & Audio, Photography, Marketing.\n\n"
                "8. AUTHENTICATION: Email/password signup, Google OAuth login, email verification, password reset via email link.\n\n"
                "9. PROFILE: Users can update username, profile picture, bio. Providers have a public profile page.\n\n"
                "10. ADMIN PANEL: Manage users (ban/unban), approve or reject skill/service submissions with a reason, manage categories.\n\n"

                "=== NAVIGATION GUIDE ===\n"
                "- Browse services: /service/browse\n"
                "- My orders (customer): /user/orders\n"
                "- My orders (provider): /user/dashboard\n"
                "- Book a session: On the service detail page, pick an available slot\n"
                "- My bookings: /user/bookings\n"
                "- Create a service listing: /service/create (must be logged in as provider)\n"
                "- View/edit a specific order: /user/order/<order_id>\n"
                "- Admin dashboard: /admin/dashboard\n"
                "- Login: /auth/login | Register: /auth/register\n"
                "- Reset password: /auth/forgot-password\n\n"

                "=== EMAIL NOTIFICATIONS SENT ===\n"
                "- Welcome email on registration\n"
                "- Order placed (to both customer and provider)\n"
                "- Order accepted (to both)\n"
                "- Order completed (to both, customer gets certificate link)\n"
                "- Booking confirmed / rejected\n"
                "- Skill/service rejected by admin (with reason)\n"
                "- Password reset link\n\n"

                "=== CURRENT PAGE CONTEXT ===\n"
                f"User is currently on: {context.get('page', 'unknown page')}\n\n"

                "=== RULES ===\n"
                "1. ONLY answer questions related to SkillVerse. For anything unrelated (coding help, general knowledge, math, news, etc.) "
                "reply exactly: 'This query is not related to SkillVerse. I can only help with platform-related questions!'\n"
                "2. NEVER invent features, prices, or statistics that aren't listed above.\n"
                "3. If asked for data you don't have (e.g. order counts, earnings), say: 'Please check your dashboard for live data.'\n"
                "4. Keep responses concise, friendly, and helpful. Use bullet points for multi-step answers.\n"
                "5. Always guide users to the correct page/URL when relevant.\n"
                "6. If the user seems confused or stuck, offer 2-3 follow-up suggestions they can ask about.\n"
                "7. Tone: Warm, professional, and encouraging."
            )
            
            response = self.model.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=300,
                top_p=0.9
            )
            
            ai_text = response.choices[0].message.content.strip()
            return {"response": ai_text, "suggestions": self.get_initial_suggestions(user_role)[:3]}
                
        except Exception as e:
            print(f"ChatManager Error: {e}")
            traceback.print_exc()
            return {"error": "I'm having trouble connecting right now.", "fallback": True}

    def get_initial_suggestions(self, role):
        if role == 'admin':
            return [
                "How do I approve a service listing?",
                "How do I manage users?",
                "How do I reject a skill submission?",
                "How do I add a new category?",
                "Where can I see all platform orders?",
            ]
        elif role == 'provider':
            return [
                "How do I create a service listing?",
                "How do I accept or reject an order?",
                "How do I set my availability slots?",
                "How do I mark an order as complete?",
                "Why was my skill submission rejected?",
            ]
        else:  # customer / guest
            return [
                "How do I place an order?",
                "How do I book a session with a provider?",
                "How do I track my order?",
                "How do I download my certificate?",
                "How do I leave a review?",
            ]

chat_manager = ChatManager()