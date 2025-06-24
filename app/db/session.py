from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings

# Tạo engine kết nối đến database
# pool_pre_ping=True giúp kiểm tra kết nối trước mỗi lần sử dụng
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Tạo một lớp SessionLocal, mỗi instance của lớp này sẽ là một phiên làm việc với database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)