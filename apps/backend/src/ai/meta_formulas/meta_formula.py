class MetaFormula:
    """
    Base class for all MetaFormulas.:
    """
在函数定义前添加空行
        self.name = name
        self.description = description

    def execute(self, *args, * * kwargs):
        """
        Executes the meta - formula.
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("This meta - formula has not been implemented yet.")
