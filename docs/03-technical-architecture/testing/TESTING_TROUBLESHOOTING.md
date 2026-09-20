# 测试问题排查指南

本文档帮助您解决运行测试时可能遇到的常见问题。

## 🚀 快速诊断

### 第一步：运行健康检查

```cmd
双击 health-check.bat
```

如果健康检查通过，但测试仍然失败，请继续阅读下面的详细排查步骤。

## 📝 常见问题及解决方案

### 1. 后端测试问题

#### 问题：Python 虚拟环境未找到

```
❌ Python 虚拟环境未找到，请先运行 start-dev.bat 进行设置
```

**解决方案：**

```cmd
# 方法1：自动设置
双击 start-dev.bat，选择任意选项进行自动设置

# 方法2：手动创建
cd apps\backend
python -m venv venv
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 问题：pytest 命令不存在

```
'pytest' 不是内部或外部命令
```

**解决方案：**

```cmd
cd apps\backend
call venv\Scripts\activate.bat
pip install pytest pytest-cov pytest-asyncio
```

#### 问题：导入错误

```
ImportError: No module named 'src'
```

**解决方案：** 检查 `apps\backend\pytest.ini` 文件中的 `pythonpath` 配置：

```ini
[pytest]
pythonpath = src
testpaths = tests
```

### 2. 前端测试问题

#### 问题：pnpm 命令失败

```
⚠️ pnpm 测试失败，尝试使用 npm...
```

**解决方案：**

```cmd
# 检查 pnpm 是否安装
pnpm --version

# 如果未安装
npm install -g pnpm

# 重新安装依赖
cd apps\frontend-dashboard
pnpm install
```

#### 问题：Jest 配置错误

```
Jest configuration error
```

**解决方案：** 检查 `apps\frontend-dashboard\jest.config.js`
文件是否存在并配置正确：

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testMatch: ['**/__tests__/**/*.{js,jsx,ts,tsx}'],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}
```

#### 问题：React 测试错误

```
ReferenceError: React is not defined
```

**解决方案：** 检查 `apps\frontend-dashboard\jest.setup.js` 文件：

```javascript
import '@testing-library/jest-dom'
```

### 3. 桌面应用测试问题

#### 问题：Electron 测试环境配置

```
Error: Electron failed to install correctly
```

**解决方案：**

```cmd
cd apps\desktop-app
npm install electron --save-dev
# 或者
pnpm add electron -D
```

#### 问题：Jest 与 Electron 兼容性

```
Jest worker encountered 4 child process exceptions
```

**解决方案：** 更新 `apps\desktop-app\jest.config.js`：

```javascript
module.exports = {
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testMatch: ['**/__tests__/**/*.{js,jsx,ts,tsx}'],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
}
```

### 4. 性能问题

#### 问题：测试运行缓慢

**解决方案：**

1. 使用快速测试模式：

   ```cmd
   # 选择 run-tests.bat 中的选项 7
   ```

2. 并行运行测试：

   ```cmd
   # 后端
   pytest -n auto  # 需要安装 pytest-xdist

   # 前端
   npm test -- --maxWorkers=50%
   ```

3. 跳过慢测试：
   ```cmd
   pytest -m "not slow"
   ```

#### 问题：内存不足

```
JavaScript heap out of memory
```

**解决方案：**

```cmd
# 增加 Node.js 内存限制
set NODE_OPTIONS=--max-old-space-size=4096
npm test
```

### 5. 网络问题

#### 问题：依赖下载失败

```
Failed to fetch package
```

**解决方案：**

```cmd
# 清除缓存并重新安装
pnpm store prune
pnpm install

# 或者使用 npm
npm cache clean --force
npm install
```

#### 问题：代理设置

如果在公司网络环境下：

```cmd
# 设置 npm 代理
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080

# 设置 pnpm 代理
pnpm config set proxy http://proxy.company.com:8080
pnpm config set https-proxy http://proxy.company.com:8080
```

## 🔍 高级排查

### 启用详细日志

```cmd
# 后端详细日志
cd apps\backend
call venv\Scripts\activate.bat
pytest -v -s --tb=long

# 前端详细日志
npm test -- --verbose

# pnpm 详细日志
pnpm test --reporter=verbose
```

### 检查依赖冲突

```cmd
# 检查 Python 依赖
pip check

# 检查 Node.js 依赖
npm ls
pnpm list
```

### 环境变量检查

```cmd
# 检查关键环境变量
echo %NODE_ENV%
echo %TESTING%
echo %PATH%
```

## 🆘 获取帮助

如果问题仍然存在：

1. **查看详细错误日志**：运行测试时不要使用 `--silent` 参数
2. **检查系统资源**：确保有足够的内存和磁盘空间
3. **重置环境**：删除 `node_modules` 和 `venv` 文件夹，重新安装
4. **查看项目文档**：阅读 `DEVELOPMENT_GUIDE.md` 获取更多信息

### 完全重置步骤

```cmd
# 1. 清理所有依赖
rmdir /s /q node_modules
rmdir /s /q apps\backend\venv
rmdir /s /q apps\frontend-dashboard\node_modules
rmdir /s /q apps\desktop-app\node_modules

# 2. 重新设置
双击 start-dev.bat
选择相应选项进行自动设置

# 3. 运行测试
双击 run-tests.bat
```

---

**提示**：建议先使用"快速测试"模式进行基础验证，然后再运行完整测试套件。
