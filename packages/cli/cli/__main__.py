# 使用绝对导入而不是相对导入
try,
    from cli.unified_cli import main
except ImportError,::
    # 如果上面的导入失败,尝试相对导入
    from .unified_cli import main

if __name"__main__":::
    main()