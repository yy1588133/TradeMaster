# 贡献指南

感谢您对TradeMaster Web Interface项目的关注！我们欢迎所有形式的贡献，包括但不限于代码贡献、问题报告、功能建议、文档改进等。

## 🤝 贡献方式

### 代码贡献
- 修复bug
- 添加新功能
- 改进现有功能
- 性能优化
- 重构代码

### 非代码贡献
- 报告bug
- 提出功能建议
- 改进文档
- 翻译内容
- 分享使用经验
- 参与讨论

## 📋 开始之前

### 先决条件
- 熟悉Git和GitHub工作流
- 了解项目使用的技术栈
- 阅读过项目文档和代码规范
- 设置好开发环境

### 有用的资源
- [项目文档](docs/README.md)
- [开发环境设置](docs/development/setup.md)
- [代码规范](docs/development/coding-standards.md)
- [架构文档](docs/architecture/system-overview.md)

## 🔍 寻找贡献机会

### 适合新手的问题
查找标有以下标签的Issues：
- `good first issue` - 适合新手的简单问题
- `help wanted` - 需要社区帮助的问题
- `documentation` - 文档相关的改进
- `bug` - 待修复的bug

### 高级贡献机会
- `enhancement` - 功能增强
- `performance` - 性能优化
- `refactoring` - 代码重构
- `architecture` - 架构改进

## 🚀 贡献流程

### 1. 准备工作

#### Fork项目
```bash
# 1. 在GitHub上Fork项目
# 2. 克隆您的Fork
git clone https://github.com/YOUR_USERNAME/trademaster-web-interface.git
cd trademaster-web-interface

# 3. 添加上游仓库
git remote add upstream https://github.com/original-org/trademaster-web-interface.git

# 4. 验证远程仓库
git remote -v
```

#### 设置开发环境
```bash
# 安装依赖并设置环境
./scripts/dev-setup.sh

# 运行测试确保环境正常
make test
```

### 2. 创建分支

```bash
# 确保主分支是最新的
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feature/your-feature-name
# 或修复bug分支
git checkout -b fix/issue-number-description
```

#### 分支命名规范
- `feature/功能名称` - 新功能
- `fix/issue编号-描述` - Bug修复
- `docs/文档类型` - 文档更新
- `refactor/重构内容` - 代码重构
- `perf/优化内容` - 性能优化
- `test/测试内容` - 测试相关

### 3. 开发

#### 开发原则
- 遵循项目的代码规范
- 编写清晰的提交消息
- 保持小而专注的提交
- 添加必要的测试
- 更新相关文档

#### 代码质量检查
```bash
# 运行代码格式化
make format

# 运行代码检查
make lint

# 运行类型检查
make type-check

# 运行测试
make test
```

### 4. 提交代码

#### 提交消息规范
我们使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<类型>[可选范围]: <描述>

[可选正文]

[可选脚注]
```

**类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档变更
- `style`: 代码格式修改
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**：
```bash
# 新功能
git commit -m "feat(user): 添加用户头像上传功能"

# Bug修复
git commit -m "fix(api): 修复用户登录时的内存泄漏问题"

# 文档更新
git commit -m "docs: 更新API文档示例"

# 重构
git commit -m "refactor(auth): 简化JWT验证逻辑"
```

#### 提交最佳实践
```bash
# 添加文件到暂存区
git add .

# 检查暂存的更改
git diff --cached

# 提交更改
git commit -m "feat(strategy): 添加策略回测功能

- 实现历史数据回测算法
- 添加回测结果可视化
- 增加风险指标计算

Closes #123"

# 推送到您的Fork
git push origin feature/your-feature-name
```

### 5. 创建Pull Request

#### PR标题格式
使用与提交消息相同的格式：
```
feat(user): 添加用户头像上传功能
```

#### PR描述模板
```markdown
## 描述
简要描述本次PR的更改内容。

## 更改类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重大变更
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 测试
- [ ] 新增测试用例
- [ ] 现有测试全部通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 自我review过代码
- [ ] 代码有适当的注释
- [ ] 相关文档已更新
- [ ] 没有新的警告产生

## 相关Issue
Closes #(issue编号)

## 截图（如适用）
添加截图来帮助解释您的更改。

## 其他说明
添加任何其他相关信息。
```

#### 创建PR
1. 访问您的GitHub Fork页面
2. 点击"Compare & pull request"
3. 填写PR标题和描述
4. 选择正确的目标分支（通常是`main`）
5. 添加适当的标签
6. 请求review

## 📝 代码审查

### 审查流程
1. **自动检查**: CI会自动运行测试和代码检查
2. **维护者审查**: 项目维护者会审查您的代码
3. **反馈处理**: 根据反馈修改代码
4. **最终批准**: 获得批准后合并到主分支

### 常见审查要点
- 代码质量和可读性
- 测试覆盖率
- 性能影响
- 安全性考虑
- 向后兼容性
- 文档完整性

### 处理审查反馈
```bash
# 拉取最新的主分支
git checkout main
git pull upstream main

# 切换到您的功能分支
git checkout feature/your-feature-name

# 合并最新的主分支（如需要）
git merge main

# 修改代码处理反馈
# ... 进行修改 ...

# 提交修改
git add .
git commit -m "fix: 处理代码审查反馈"

# 推送更新
git push origin feature/your-feature-name
```

## 🐛 问题报告

### 报告Bug

#### 使用Issue模板
我们提供了Issue模板来帮助您提供必要信息：

```markdown
**问题描述**
清晰简洁地描述bug。

**复现步骤**
1. 前往 '...'
2. 点击 '....'
3. 向下滚动到 '....'
4. 看到错误

**期望行为**
清晰简洁地描述您期望发生的事情。

**实际行为**
清晰简洁地描述实际发生的事情。

**截图**
如果适用，添加截图来帮助解释您的问题。

**环境信息**
- OS: [e.g. Windows 11, macOS 13.0, Ubuntu 20.04]
- 浏览器: [e.g. Chrome 100.0, Firefox 99.0, Safari 15.0]
- Node.js版本: [e.g. 18.15.0]
- Python版本: [e.g. 3.9.16]

**附加信息**
添加任何其他相关信息。
```

#### Bug报告最佳实践
- 使用描述性标题
- 提供详细的复现步骤
- 包含错误消息和日志
- 附上相关截图或视频
- 说明环境信息
- 检查是否已有相似问题

### 功能建议

#### 建议模板
```markdown
**功能描述**
清晰简洁地描述您建议的功能。

**问题背景**
这个功能解决了什么问题？是否与现有功能相关？

**解决方案**
描述您想要的解决方案。

**替代方案**
描述您考虑过的其他替代解决方案。

**用户故事**
从用户角度描述功能使用场景。

**附加信息**
添加任何其他相关信息、截图或示例。
```

## 🧪 测试指南

### 测试要求
- 所有新功能必须有测试
- Bug修复必须包含回归测试
- 测试覆盖率应保持或提高
- 测试应该清晰且可维护

### 测试类型
```bash
# 单元测试
make test-unit

# 集成测试
make test-integration

# E2E测试
make test-e2e

# 所有测试
make test
```

### 编写测试
- 使用描述性的测试名称
- 遵循AAA模式（Arrange-Act-Assert）
- 测试边界条件和错误情况
- 保持测试独立性

## 🌍 国际化

### 添加翻译
1. 在相应的语言文件中添加翻译
2. 使用标准的本地化格式
3. 确保翻译准确且文化适宜
4. 测试不同语言下的UI

### 支持的语言
- 简体中文 (zh-CN)
- 繁体中文 (zh-TW)
- 英语 (en-US)
- 日语 (ja-JP)

## 📚 文档贡献

### 文档类型
- 用户文档
- 开发者文档
- API文档
- 教程和示例
- 故障排除指南

### 文档规范
- 使用清晰的标题结构
- 提供代码示例
- 包含相关截图
- 保持更新同步
- 使用一致的风格

## 🎯 成为维护者

### 维护者职责
- 审查Pull Request
- 回复Issues
- 维护项目质量
- 制定技术决策
- 指导新贡献者

### 成为维护者的路径
1. **活跃贡献**: 持续贡献高质量代码
2. **社区参与**: 积极参与讨论和帮助他人
3. **技术专长**: 展示技术能力和判断力
4. **责任感**: 表现出对项目的长期承诺
5. **推荐**: 获得现有维护者的推荐

## 🏆 认可贡献者

### 贡献者类型
- **代码贡献者**: 提交代码的开发者
- **问题报告者**: 报告bug和问题的用户
- **文档维护者**: 改进文档的贡献者
- **社区支持者**: 帮助其他用户的志愿者
- **翻译者**: 提供本地化支持的译者

### 认可方式
- 在CONTRIBUTORS.md中列出
- 在发布说明中致谢
- 社交媒体宣传
- 会议演讲机会
- 特殊徽章和称号

## 🚫 不被接受的贡献

### 不接受的内容
- 违反开源许可证的代码
- 包含恶意内容的提交
- 大幅偏离项目目标的功能
- 质量极低的代码
- 缺乏测试的重要功能
- 破坏现有功能的更改

### 被拒绝的原因
- 与项目愿景不符
- 代码质量不达标
- 缺乏适当的测试
- 文档不完整
- 引入安全风险
- 维护成本过高

## 📞 获取帮助

### 联系方式
- **GitHub Issues**: 报告问题和功能请求
- **GitHub Discussions**: 一般讨论和问答
- **邮件**: core-team@trademaster.example.com
- **官方网站**: https://trademaster.example.com

### 社区支持
- **Discord**: https://discord.gg/trademaster
- **微信群**: 扫描项目README中的二维码
- **QQ群**: 123456789
- **论坛**: https://forum.trademaster.example.com

## 📄 行为准则

### 我们的承诺
为了营造开放和欢迎的环境，我们作为贡献者和维护者承诺，无论年龄、体型、残疾、种族、性别认同和表达、经验水平、国籍、个人形象、种族、宗教或性取向，参与我们项目和社区的每个人都将获得无骚扰的体验。

### 行为标准
有助于创造积极环境的行为包括：
- 使用欢迎和包容性语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表现出同理心

### 不被接受的行为
- 使用性化语言或图像以及不受欢迎的性关注或骚扰
- 挑衅、侮辱/贬损评论，以及个人或政治攻击
- 公开或私下骚扰
- 未经明确许可发布他人的私人信息
- 在专业环境中被合理认为不合适的其他行为

### 执行
可以通过core-team@trademaster.example.com联系项目团队来报告滥用、骚扰或其他不被接受的行为。所有投诉都将被审查和调查，并将导致被认为必要和适当的回应。

## 🎉 致谢

感谢所有为TradeMaster Web Interface做出贡献的人！

### 特别感谢
- 所有代码贡献者
- 问题报告者和测试人员
- 文档维护者
- 社区支持者
- 翻译志愿者

### 灵感来源
本项目受到以下优秀开源项目的启发：
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)
- [TradingView](https://www.tradingview.com/)

---

再次感谢您的贡献！让我们一起构建更好的TradeMaster Web Interface！ 🚀

<div align="center">
  <sub>
    Built with ❤️ by the TradeMaster community
  </sub>
</div>