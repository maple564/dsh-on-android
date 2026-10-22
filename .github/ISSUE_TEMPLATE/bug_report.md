---
name: Bug report / 跑不通
about: 装不上、起不来、白屏 —— 带上体检信息
title: "[bug] "
labels: bug
---

**发生了什么**
<!-- 一句话描述 -->

**完整报错**

```
粘贴完整报错，不要截断
```

**体检输出**

```bash
uname -a
ldd --version 2>&1 | head -1
node -v
dsh --version
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3080/
```

```
粘贴上面五条的输出
```

**环境**
- 机型 / Android 版本：
- 容器：Minis / proot-distro / UserLAnd / 其他
- 发行版：Alpine x.x
- 已尝试过的解法：
