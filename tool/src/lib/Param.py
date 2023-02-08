class Param:
    def __init__(self, name, param_line, param_col, param_type,
                 default_val, value_range, steps=None):
        self.name = name
        self.param_line=param_line
        self.param_col=param_col
        self.param_type=param_type
        self.param_default=default_val
        self.value_range = value_range
        self.step = steps

    def __str__(self):
        return "{0} : {1} : {2} : {3} : {4}".format(self.name, self.param_line, self.param_col, self.param_default, self.param_type)
