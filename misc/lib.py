class Rectangle(object):

    def __init__(self, point_lt: tuple[int, int], point_rb: tuple[int, int]):
        self.point_lt = point_lt
        self.point_rb = point_rb

    @property
    def width(self):
        return self.point_rb[0] - self.point_lt[0] 
    
    @property
    def height(self):
        return self.point_rb[1] - self.point_lt[1]
    
    @property
    def x(self):
        return self.point_lt[0]
    
    @property
    def y(self):
        return self.point_lt[1]

    @property
    def centre(self):
        return tuple((i+j)//2 for i,j in zip(self.point_lt, self.point_rb))