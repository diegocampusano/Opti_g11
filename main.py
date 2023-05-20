import gurobipy as gp
from modelador import *


def main(n_ex, n_tec, t_mes, n_pl, n_m, n):
    ### FUNCION OBJETIVO ###
    modelo, obj = modelador(n_ex, n_tec, t_mes, n_pl, n_m, n)
    modelo.update()
    modelo.setObjective(obj, gp.GRB.MINIMIZE)
    modelo.optimize()
    # imprime los coeficientes de las variables
#     modelo.printAttr('obj')
    # imprime los valores de las variables
    modelo.printAttr('X')
    return
    
if __name__ == "__main__":
    main(n_ex=5, n_tec=5, t_mes=36, n_pl=3, n_m=3, n='Restricciones Entrega 2 V1')
