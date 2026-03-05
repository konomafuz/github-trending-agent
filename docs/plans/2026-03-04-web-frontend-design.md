# GitHub Trending 可视化平台 - 设计文档

**日期**: 2026-03-04
**状态**: 已批准
**作者**: Claude Code

## 1. 概述

为 GitHub Trending 商业化分析项目添加 Web 前端展示页面，替代当前仅通过 Telegram 查看的方式。用户可以通过网页浏览最新分析、查看历史归档、收藏感兴趣的仓库，并通过多维度分类探索项目。

## 2. 技术架构

### 2.1 前端技术栈
- **框架**: Vue 3 + Vite + TypeScript
- **样式**: Tailwind CSS
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI 组件**: 自定义组件 + Headless UI

### 2.2 数据处理
- **数据源**: Python 脚本生成的 Markdown 报告
- **数据格式**: JSON（从 MD 转换而来）
- **数据生成**: 在 `main.py` 中同时生成 MD 和 JSON

### 2.3 认证与存储
- **用户认证**: GitHub OAuth App
- **收藏存储**: GitHub Gist API（云端同步）
- **本地缓存**: localStorage（离线访问）

### 2.4 部署方式
- **托管平台**: GitHub Pages
- **自动化**: GitHub Actions（分析 + 构建 + 部署）
- **访问地址**: `https://konomafuz.github.io/github-trending-agent/`

## 3. 页面结构与组件设计

### 3.1 主要页面

#### 首页（Latest）
- 展示最新一期的分析报告
- 新增仓库带有 "NEW" 标签高亮
- 卡片式布局，每个仓库一张卡片
- 顶部显示：日期、总数、筛选器、搜索框

#### 归档页（Archive）
- 多维度分类浏览（见 3.3 节）
- 支持多条件组合筛选
- 左侧：分类树（可展开/折叠）
- 右侧：仓库列表

#### 收藏页（Favorites）
- 展示用户收藏的所有仓库
- 支持添加个人笔记
- 可以按收藏时间、Stars 排序
- 需要 GitHub 登录

### 3.2 核心组件

- **RepoCard**: 仓库卡片组件
  - 显示：名称、描述、Stars、语言、商业化评分
  - 操作：收藏按钮、查看详情
  - 状态：NEW 标签（新增仓库）

- **FilterBar**: 筛选器组件
  - 语言筛选（多选）
  - 商业化评分范围
  - Stars 范围滑块

- **SearchBox**: 搜索组件
  - 支持仓库名、描述、技术栈搜索
  - 实时搜索结果

- **CategoryTree**: 分类树组件
  - 多级分类展示
  - 支持展开/折叠
  - 显示每个分类的仓库数量

- **LoginButton**: GitHub 登录组件
  - OAuth 授权流程
  - 显示用户头像和名称

### 3.3 归档页分类维度

#### 按商业化潜力
- 🔥 高潜力（4-5分）：适合立即商业化
- 💡 中等潜力（2-3分）：需要进一步评估
- 📊 观察中（1分或未评分）

#### 按目标客户群体
- 👨‍💻 开发者工具（CLI、IDE、框架）
- 🏢 企业服务（SaaS、协作工具）
- 🤖 AI/ML 应用
- 📱 消费者应用
- 🔧 基础设施（数据库、中间件）

#### 按技术领域
- AI/机器学习
- 前端/UI
- 后端/API
- DevOps/部署
- 数据处理
- 安全/隐私

#### 按编程语言
- Python, JavaScript/TypeScript, Rust, Go, Java 等

#### 按 Stars 热度
- 🌟 超热门（50k+）
- ⭐ 热门（10k-50k）
- ✨ 流行（5k-10k）
- 💫 新兴（1k-5k）

#### 按技术复杂度
- 简单（易于二次开发）
- 中等
- 复杂（需要深度技术）

### 3.4 UI 设计风格
- 类似 Product Hunt 的现代卡片式设计
- 深色/浅色主题切换
- 响应式布局（支持移动端）
- 流畅的动画过渡

## 4. 数据流设计

### 4.1 数据生成流程（方案 A：一键生成）

```
运行 python main.py
    ↓
同时生成两个文件：
  - reports/YYYY-MM-DD.md（现有的）
  - web/public/data/latest.json（新增）
    ↓
本地开发：npm run dev → 立即看到结果
GitHub Actions：自动构建部署
```

### 4.2 数据结构设计

**reports.json 结构**：
```json
{
  "latest": "2026-03-04",
  "reports": {
    "2026-03-04": {
      "date": "2026-03-04",
      "repos": [
        {
          "owner": "obra",
          "name": "superpowers",
          "full_name": "obra/superpowers",
          "description": "...",
          "language": "Shell",
          "stars": 69559,
          "stars_today": 9010,
          "forks": 5341,
          "license": "MIT",
          "topics": ["..."],
          "readme_excerpt": "...",
          "analysis": {
            "gong_neng_ding_wei": "...",
            "shang_ye_hua_qian_li": 4,
            "jing_pin_saas": "...",
            "er_ci_kai_fa": ["...", "...", "..."],
            "mu_biao_ke_hu": "...",
            "ji_shu_fu_za_du": "...",
            "tui_jian_xing_dong": "..."
          }
        }
      ],
      "newRepos": ["obra/superpowers", "ruvnet/RuView"],
      "metadata": {
        "total": 19,
        "analyzed_at": "2026-03-04T02:00:00Z"
      }
    }
  },
  "categories": {
    "byLanguage": {
      "Python": ["owner/name1", "owner/name2"],
      "Rust": ["owner/name3"]
    },
    "byPotential": {
      "high": ["owner/name1"],
      "medium": ["owner/name2"],
      "low": ["owner/name3"]
    },
    "byCustomer": {
      "developers": ["owner/name1"],
      "enterprise": ["owner/name2"]
    }
  }
}
```

### 4.3 新增标记逻辑
- 对比前一天的报告，标记首次出现的仓库
- 在 `newRepos` 数组中记录新增仓库的 full_name
- 前端根据 `newRepos` 显示 "NEW" 标签

### 4.4 收藏功能实现

**流程**：
1. 用户点击"登录" → GitHub OAuth 授权
2. 获取 access token（存储在 localStorage）
3. 收藏时：调用 GitHub Gist API 创建/更新 `github-trending-favorites.json`
4. 读取时：从 Gist 获取收藏列表
5. 离线时：使用 localStorage 缓存

**Gist 数据结构**：
```json
{
  "favorites": [
    {
      "full_name": "obra/superpowers",
      "starred_at": "2026-03-04T10:30:00Z",
      "note": "用户添加的笔记"
    }
  ]
}
```

## 5. 部署流程

### 5.1 GitHub Actions 工作流

```yaml
name: Build and Deploy

on:
  schedule:
    - cron: '0 2 * * *'  # 每天 UTC 02:00
  workflow_dispatch:

jobs:
  analyze-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run analysis
        run: |
          pip install -r requirements.txt
          python main.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build frontend
        run: |
          cd web
          npm install
          npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web/dist

      - name: Send Telegram notification
        run: python -m src.notifier
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### 5.2 本地开发流程

```bash
# 1. 生成数据
python main.py

# 2. 启动前端开发服务器
cd web
npm install
npm run dev

# 3. 浏览器访问 http://localhost:5173
```

## 6. 错误处理

### 6.1 数据加载
- **JSON 加载失败**: 显示友好提示，提供重试按钮
- **数据格式错误**: 使用默认值，记录错误日志

### 6.2 用户认证
- **GitHub 登录失败**: 提示用户检查网络或重新授权
- **Token 过期**: 自动跳转到登录页面

### 6.3 收藏功能
- **Gist 创建失败**: 本地缓存，下次同步时重试
- **网络离线**: 使用 localStorage 缓存，显示"离线模式"提示

### 6.4 分类数据
- **分类字段缺失**: 使用默认分类"其他"
- **分析数据不完整**: 显示"待分析"占位符

## 7. 项目结构

```
github-trending-agent/
├── src/                    # Python 后端（现有）
│   ├── scraper.py
│   ├── enricher.py
│   ├── analyzer.py
│   ├── reporter.py
│   ├── notifier.py
│   └── json_exporter.py    # 新增：JSON 导出模块
├── reports/                # MD 报告（现有）
├── web/                    # Vue 前端（新增）
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── LatestView.vue
│   │   │   ├── ArchiveView.vue
│   │   │   └── FavoritesView.vue
│   │   ├── components/     # 可复用组件
│   │   │   ├── RepoCard.vue
│   │   │   ├── FilterBar.vue
│   │   │   ├── SearchBox.vue
│   │   │   ├── CategoryTree.vue
│   │   │   └── LoginButton.vue
│   │   ├── stores/         # Pinia 状态管理
│   │   │   ├── reports.ts
│   │   │   ├── favorites.ts
│   │   │   └── auth.ts
│   │   ├── utils/          # 工具函数
│   │   │   ├── github-auth.ts
│   │   │   ├── gist-api.ts
│   │   │   └── category.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   │   └── data/           # JSON 数据文件
│   │       └── latest.json
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── docs/
│   └── plans/
│       └── 2026-03-04-web-frontend-design.md
├── .github/
│   └── workflows/
│       └── daily_analysis.yml  # 更新：添加前端构建步骤
├── main.py                 # 更新：添加 JSON 导出调用
└── requirements.txt

```

## 8. 实现优先级

### Phase 1: 核心功能（MVP）
1. 数据导出：在 `main.py` 中添加 JSON 导出
2. Vue 项目搭建：初始化 Vite + Vue 3 + TypeScript
3. 首页实现：展示最新报告，基础卡片布局
4. 基础筛选：语言、Stars 范围

### Phase 2: 增强功能
1. 归档页：多维度分类浏览
2. 搜索功能：全文搜索
3. 新增标记：对比历史数据
4. 响应式设计：移动端适配

### Phase 3: 高级功能
1. GitHub 登录：OAuth 集成
2. 收藏功能：Gist 存储
3. 主题切换：深色/浅色模式
4. 性能优化：虚拟滚动、懒加载

## 9. 成功标准

- ✅ 运行 `python main.py` 后，前端能立即显示最新数据
- ✅ 支持按 6 种维度分类浏览历史仓库
- ✅ 新增仓库有明显的 "NEW" 标签
- ✅ 用户可以通过 GitHub 登录并收藏仓库
- ✅ 收藏数据在多设备间同步
- ✅ 移动端访问体验良好
- ✅ GitHub Actions 自动化部署成功

## 10. 风险与限制

### 10.1 风险
- **GitHub API 限流**: OAuth 用户每小时 5000 次请求，足够使用
- **Gist 大小限制**: 单个 Gist 最大 10MB，收藏数据远小于此
- **GitHub Pages 限流**: 每月 100GB 流量，静态站点足够

### 10.2 限制
- 收藏功能需要 GitHub 登录，未登录用户只能本地收藏
- 历史数据依赖 `reports/` 目录，删除 MD 文件会导致归档缺失
- 分类依赖 AI 分析质量，分析失败的仓库会归入"其他"

## 11. 未来扩展

- **数据分析**: 添加趋势图表（Stars 增长曲线）
- **社交功能**: 分享收藏列表
- **通知功能**: 关注特定语言/领域的新仓库
- **API 接口**: 提供 RESTful API 供第三方使用
- **浏览器插件**: 在 GitHub 页面直接显示商业化分析
