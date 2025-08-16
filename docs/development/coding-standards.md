# 代码规范指南

本文档规定了TradeMaster Web Interface项目的代码规范和最佳实践。

## 🎯 总体原则

### 代码质量原则
- **可读性优先**: 代码应该易于理解和维护
- **一致性**: 在整个项目中保持一致的风格
- **简洁性**: 避免不必要的复杂性
- **文档化**: 重要的逻辑应该有清晰的注释
- **测试驱动**: 所有代码都应该有相应的测试

### SOLID 原则
- **单一职责原则** (SRP): 每个类只有一个改变的理由
- **开闭原则** (OCP): 对扩展开放，对修改关闭
- **里氏替换原则** (LSP): 子类必须能够替换父类
- **接口隔离原则** (ISP): 不应该强迫客户端依赖它们不使用的接口
- **依赖倒置原则** (DIP): 高层模块不应该依赖低层模块

## 🐍 Python 代码规范 (后端)

### 基本规范

我们遵循 [PEP 8](https://pep8.org/) 和 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)。

#### 代码格式化

```python
# 使用 Black 自动格式化
black .

# 使用 isort 排序导入
isort .

# 使用 autoflake 删除未使用的导入
autoflake --remove-all-unused-imports --in-place --recursive .
```

#### 导入规范

```python
# 标准库导入
import os
import sys
from typing import List, Dict, Optional

# 第三方库导入
import fastapi
import sqlalchemy
from fastapi import Depends, HTTPException

# 本地导入
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate
```

#### 命名规范

```python
# 常量：全大写，下划线分隔
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 变量和函数：小写，下划线分隔
user_name = "john_doe"
max_items = 100

def get_user_by_id(user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    pass

# 类名：首字母大写的驼峰式
class UserService:
    """用户服务类"""
    pass

# 私有属性/方法：单下划线前缀
class MyClass:
    def __init__(self):
        self._private_attr = "private"
    
    def _private_method(self):
        pass
```

### 类型注解

```python
from typing import List, Dict, Optional, Union, Any

def process_user_data(
    user_id: int,
    user_data: Dict[str, Any],
    include_deleted: bool = False
) -> Optional[User]:
    """处理用户数据"""
    pass

class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db: Session) -> None:
        self.db = db
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """获取用户列表"""
        pass
```

### 错误处理

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        try:
            # 业务逻辑
            user = await self.user_repo.create(user_data)
            logger.info(f"用户创建成功: {user.id}")
            return user
        
        except IntegrityError as e:
            logger.error(f"用户创建失败 - 数据完整性错误: {e}")
            raise HTTPException(
                status_code=400,
                detail="用户已存在"
            )
        
        except Exception as e:
            logger.error(f"用户创建失败 - 未知错误: {e}")
            raise HTTPException(
                status_code=500,
                detail="内部服务器错误"
            )
```

### FastAPI 规范

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户账户"
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    """
    创建新用户
    
    Args:
        user_data: 用户创建数据
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        创建的用户对象
    
    Raises:
        HTTPException: 用户创建失败时抛出
    """
    service = UserService(db)
    return await service.create_user(user_data)
```

### 数据库规范

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本字段
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    
    # 状态字段
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # 时间戳字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
```

### 测试规范

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.deps import get_db
from tests.utils.user import create_random_user
from tests.utils.utils import random_email, random_lower_string

class TestUserAPI:
    """用户API测试类"""
    
    def test_create_user_success(self, client: TestClient, db: Session):
        """测试用户创建成功场景"""
        # Arrange
        user_data = {
            "username": random_lower_string(),
            "email": random_email(),
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/users/", json=user_data)
        
        # Assert
        assert response.status_code == 201
        created_user = response.json()
        assert created_user["username"] == user_data["username"]
        assert created_user["email"] == user_data["email"]
        assert "id" in created_user
    
    def test_create_user_duplicate_email(self, client: TestClient, db: Session):
        """测试重复邮箱创建用户失败场景"""
        # Arrange
        existing_user = create_random_user(db)
        user_data = {
            "username": random_lower_string(),
            "email": existing_user.email,  # 重复邮箱
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/users/", json=user_data)
        
        # Assert
        assert response.status_code == 400
        assert "已存在" in response.json()["detail"]
```

## ⚛️ TypeScript/React 代码规范 (前端)

### 基本规范

我们遵循 [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) 和 [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)。

#### 命名规范

```typescript
// 常量：全大写，下划线分隔
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'http://localhost:8000';

// 变量和函数：驼峰式
const userName = 'john_doe';
const maxItems = 100;

const getUserById = async (userId: number): Promise<User | null> => {
  // 函数实现
};

// 类型和接口：首字母大写的驼峰式
interface User {
  id: number;
  username: string;
  email: string;
}

type UserStatus = 'active' | 'inactive' | 'pending';

// 组件：首字母大写的驼峰式
const UserProfile: React.FC<UserProfileProps> = ({ user }) => {
  return <div>{user.username}</div>;
};

// 枚举：首字母大写的驼峰式
enum UserRole {
  Admin = 'admin',
  User = 'user',
  Guest = 'guest',
}
```

#### 类型定义

```typescript
// 基础类型定义
interface User {
  id: number;
  username: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// API 响应类型
interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

// 分页类型
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 表单类型
interface UserCreateForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

// 组件 Props 类型
interface UserProfileProps {
  user: User;
  onEdit?: (user: User) => void;
  onDelete?: (userId: number) => void;
  className?: string;
}
```

### React 组件规范

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import { Button, Card, message } from 'antd';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { userActions } from '@/store/slices/userSlice';
import type { User } from '@/types/user';

interface UserProfileProps {
  userId: number;
  onUpdate?: (user: User) => void;
}

/**
 * 用户资料组件
 * 
 * @param userId - 用户ID
 * @param onUpdate - 更新回调函数
 */
const UserProfile: React.FC<UserProfileProps> = ({ 
  userId, 
  onUpdate 
}) => {
  // 状态定义
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  
  // Redux 状态
  const dispatch = useAppDispatch();
  const user = useAppSelector(state => 
    state.user.users.find(u => u.id === userId)
  );
  
  // 副作用
  useEffect(() => {
    if (!user) {
      dispatch(userActions.fetchUser(userId));
    }
  }, [dispatch, userId, user]);
  
  // 事件处理
  const handleEdit = useCallback(() => {
    setEditing(true);
  }, []);
  
  const handleSave = useCallback(async (userData: Partial<User>) => {
    try {
      setLoading(true);
      const updatedUser = await dispatch(
        userActions.updateUser({ id: userId, ...userData })
      ).unwrap();
      
      message.success('用户信息更新成功');
      onUpdate?.(updatedUser);
      setEditing(false);
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [dispatch, userId, onUpdate]);
  
  // 渲染
  if (!user) {
    return <div>加载中...</div>;
  }
  
  return (
    <Card 
      title="用户资料"
      extra={
        <Button 
          type="primary" 
          onClick={handleEdit}
          disabled={editing}
        >
          编辑
        </Button>
      }
      loading={loading}
    >
      <div className="user-profile">
        <div className="user-info">
          <p><strong>用户名:</strong> {user.username}</p>
          <p><strong>邮箱:</strong> {user.email}</p>
          <p><strong>状态:</strong> {user.isActive ? '激活' : '未激活'}</p>
        </div>
        
        {editing && (
          <UserEditForm 
            user={user}
            onSave={handleSave}
            onCancel={() => setEditing(false)}
          />
        )}
      </div>
    </Card>
  );
};

export default UserProfile;
```

### 自定义 Hook 规范

```typescript
import { useState, useEffect, useCallback } from 'react';
import { useAppDispatch } from '@/store/hooks';
import { userActions } from '@/store/slices/userSlice';
import type { User, UserCreateForm } from '@/types/user';

interface UseUserManagerOptions {
  autoFetch?: boolean;
  pageSize?: number;
}

interface UseUserManagerReturn {
  users: User[];
  loading: boolean;
  error: string | null;
  createUser: (userData: UserCreateForm) => Promise<User>;
  updateUser: (id: number, userData: Partial<User>) => Promise<User>;
  deleteUser: (id: number) => Promise<void>;
  fetchUsers: (page?: number) => Promise<void>;
}

/**
 * 用户管理自定义Hook
 * 
 * @param options - 配置选项
 * @returns 用户管理相关的状态和方法
 */
export const useUserManager = (
  options: UseUserManagerOptions = {}
): UseUserManagerReturn => {
  const { autoFetch = true, pageSize = 20 } = options;
  
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  
  // 获取用户列表
  const fetchUsers = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await dispatch(
        userActions.fetchUsers({ page, size: pageSize })
      ).unwrap();
      
      setUsers(result.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取用户失败');
    } finally {
      setLoading(false);
    }
  }, [dispatch, pageSize]);
  
  // 创建用户
  const createUser = useCallback(async (userData: UserCreateForm) => {
    try {
      setLoading(true);
      const newUser = await dispatch(
        userActions.createUser(userData)
      ).unwrap();
      
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建用户失败');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  // 更新用户
  const updateUser = useCallback(async (
    id: number, 
    userData: Partial<User>
  ) => {
    try {
      setLoading(true);
      const updatedUser = await dispatch(
        userActions.updateUser({ id, ...userData })
      ).unwrap();
      
      setUsers(prev => 
        prev.map(user => user.id === id ? updatedUser : user)
      );
      
      return updatedUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新用户失败');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  // 删除用户
  const deleteUser = useCallback(async (id: number) => {
    try {
      setLoading(true);
      await dispatch(userActions.deleteUser(id)).unwrap();
      setUsers(prev => prev.filter(user => user.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除用户失败');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  // 自动获取数据
  useEffect(() => {
    if (autoFetch) {
      fetchUsers();
    }
  }, [autoFetch, fetchUsers]);
  
  return {
    users,
    loading,
    error,
    createUser,
    updateUser,
    deleteUser,
    fetchUsers,
  };
};
```

### Redux Toolkit 规范

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { User, UserCreateForm } from '@/types/user';
import { userApi } from '@/services/userApi';

// 异步 Action
export const fetchUsers = createAsyncThunk(
  'user/fetchUsers',
  async (params: { page: number; size: number }) => {
    const response = await userApi.getUsers(params);
    return response.data;
  }
);

export const createUser = createAsyncThunk(
  'user/createUser',
  async (userData: UserCreateForm, { rejectWithValue }) => {
    try {
      const response = await userApi.createUser(userData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.message || '创建失败');
    }
  }
);

// State 类型
interface UserState {
  users: User[];
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
}

// 初始状态
const initialState: UserState = {
  users: [],
  loading: false,
  error: null,
  total: 0,
  currentPage: 1,
};

// Slice
const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    // 同步 Action
    clearError: (state) => {
      state.error = null;
    },
    
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    
    updateUserInList: (state, action: PayloadAction<User>) => {
      const index = state.users.findIndex(u => u.id === action.payload.id);
      if (index !== -1) {
        state.users[index] = action.payload;
      }
    },
  },
  extraReducers: (builder) => {
    // 获取用户列表
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取用户失败';
      });
    
    // 创建用户
    builder
      .addCase(createUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(createUser.fulfilled, (state, action) => {
        state.loading = false;
        state.users.push(action.payload);
      })
      .addCase(createUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const userActions = {
  ...userSlice.actions,
  fetchUsers,
  createUser,
};

export default userSlice.reducer;
```

## 🧪 测试规范

### 测试原则

- **测试金字塔**: 单元测试 > 集成测试 > E2E测试
- **测试覆盖率**: 目标 >80%
- **测试命名**: 描述性命名，说明测试场景
- **AAA模式**: Arrange（准备）-> Act（执行）-> Assert（断言）

### 前端测试规范

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import userEvent from '@testing-library/user-event';

import UserProfile from '@/components/UserProfile';
import userReducer from '@/store/slices/userSlice';
import { mockUser } from '@/test/mocks/user';

// 测试工具函数
const renderWithRedux = (
  component: React.ReactElement,
  initialState = {}
) => {
  const store = configureStore({
    reducer: {
      user: userReducer,
    },
    preloadedState: initialState,
  });
  
  return {
    ...render(
      <Provider store={store}>
        {component}
      </Provider>
    ),
    store,
  };
};

describe('UserProfile', () => {
  const defaultProps = {
    userId: 1,
    onUpdate: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  describe('渲染测试', () => {
    it('应该正确渲染用户信息', () => {
      // Arrange
      const initialState = {
        user: {
          users: [mockUser],
          loading: false,
          error: null,
        },
      };
      
      // Act
      renderWithRedux(
        <UserProfile {...defaultProps} />,
        initialState
      );
      
      // Assert
      expect(screen.getByText('用户资料')).toBeInTheDocument();
      expect(screen.getByText(mockUser.username)).toBeInTheDocument();
      expect(screen.getByText(mockUser.email)).toBeInTheDocument();
    });
    
    it('用户不存在时应该显示加载状态', () => {
      // Arrange
      const initialState = {
        user: {
          users: [],
          loading: false,
          error: null,
        },
      };
      
      // Act
      renderWithRedux(
        <UserProfile {...defaultProps} />,
        initialState
      );
      
      // Assert
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });
  
  describe('交互测试', () => {
    it('点击编辑按钮应该进入编辑模式', async () => {
      // Arrange
      const user = userEvent.setup();
      const initialState = {
        user: {
          users: [mockUser],
          loading: false,
          error: null,
        },
      };
      
      renderWithRedux(
        <UserProfile {...defaultProps} />,
        initialState
      );
      
      // Act
      const editButton = screen.getByRole('button', { name: /编辑/ });
      await user.click(editButton);
      
      // Assert
      await waitFor(() => {
        expect(screen.getByTestId('user-edit-form')).toBeInTheDocument();
      });
    });
  });
  
  describe('错误处理测试', () => {
    it('更新失败时应该显示错误消息', async () => {
      // Arrange
      const user = userEvent.setup();
      const mockUpdateUser = jest.fn().mockRejectedValue(
        new Error('更新失败')
      );
      
      // Mock Redux action
      jest.mock('@/store/slices/userSlice', () => ({
        userActions: {
          updateUser: mockUpdateUser,
        },
      }));
      
      const initialState = {
        user: {
          users: [mockUser],
          loading: false,
          error: null,
        },
      };
      
      renderWithRedux(
        <UserProfile {...defaultProps} />,
        initialState
      );
      
      // Act
      const editButton = screen.getByRole('button', { name: /编辑/ });
      await user.click(editButton);
      
      const saveButton = screen.getByRole('button', { name: /保存/ });
      await user.click(saveButton);
      
      // Assert
      await waitFor(() => {
        expect(screen.getByText('更新失败，请重试')).toBeInTheDocument();
      });
    });
  });
});
```

## 📋 代码审查清单

### 通用检查项

- [ ] 代码遵循项目规范
- [ ] 命名清晰有意义
- [ ] 函数和类职责单一
- [ ] 异常处理完善
- [ ] 日志记录适当
- [ ] 测试覆盖充分
- [ ] 文档注释完整
- [ ] 性能影响评估

### Python 特定检查

- [ ] 类型注解正确
- [ ] 导入顺序规范
- [ ] 数据库事务处理
- [ ] 异步代码正确使用
- [ ] 安全漏洞检查

### TypeScript/React 特定检查

- [ ] 组件设计合理
- [ ] 状态管理恰当
- [ ] 副作用处理正确
- [ ] 性能优化考虑
- [ ] 可访问性支持

## 🛠️ 工具集成

### 代码格式化工具

```bash
# Python
black .                 # 代码格式化
isort .                 # 导入排序
autoflake --remove-all-unused-imports --in-place --recursive .

# TypeScript/JavaScript
prettier --write .      # 代码格式化
eslint --fix .          # 代码检查和修复
```

### 代码质量检查

```bash
# Python
flake8 .               # 代码风格检查
mypy .                 # 类型检查
bandit -r .            # 安全检查

# TypeScript/JavaScript
eslint .               # 代码检查
tsc --noEmit          # 类型检查
```

### Pre-commit 配置

项目已配置 pre-commit hooks，会在提交前自动运行：

- 代码格式化
- 代码质量检查
- 测试运行
- 安全扫描

## 📚 参考资源

### Python 相关

- [PEP 8 - Python代码风格指南](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI 最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy 最佳实践](https://docs.sqlalchemy.org/en/14/orm/tutorial.html)

### TypeScript/React 相关

- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Redux Toolkit 最佳实践](https://redux-toolkit.js.org/usage/usage-guide)
- [Testing Library 最佳实践](https://testing-library.com/docs/guiding-principles)

### 通用规范

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git 工作流最佳实践](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

遵循这些规范将帮助我们构建高质量、可维护的代码。如有疑问，请在团队中讨论或查阅相关文档。