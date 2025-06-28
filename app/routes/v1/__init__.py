from app.routes.base import BaseRouter
from app.routes.v1.auth import AuthRouter
from app.routes.v1.carts import CartRouter
from app.routes.v1.categories import CategoryRouter
from app.routes.v1.products import ProductRouter
from app.routes.v1.profile import ProfileRouter
from app.routes.v1.registration import RegisterRouter
from app.routes.v1.users import UserRouter
from app.routes.v1.verification import VerificationRouter


class APIv1(BaseRouter):
    def configure_routes(self):
        self.router.include_router(RegisterRouter().get_router())
        self.router.include_router(AuthRouter().get_router())
        self.router.include_router(VerificationRouter().get_router())
        self.router.include_router(UserRouter().get_router())
        self.router.include_router(ProfileRouter().get_router())
        self.router.include_router(CategoryRouter().get_router())
        self.router.include_router(ProductRouter().get_router())
        self.router.include_router(CartRouter().get_router())
