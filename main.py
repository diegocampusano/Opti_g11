import gurobipy as gp
from modelador import *


def main(n_ex, n_tec, t_mes):
    ### FUNCION OBJETIVO ###
    modelo, obj = modelador(n_ex, n_tec, t_mes)
    modelo.update()
    modelo.setObjective(obj, gp.GRB.MINIMIZE)
    modelo.optimize()
    # imprime los coeficientes de las variables
    # modelo.printAttr('obj')
    # imprime los valores de las variables
    modelo.printAttr('X')
    return
    
if __name__ == "__main__":
    main(n_ex=5, n_tec=5, t_mes=36)
