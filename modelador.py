import gurobipy as gp
from random import randint, choices, seed
import numpy as np


def modelador(n_ex, n_tec, t_mes, n_pl, n_m, n='V3'):
    """Función que define el dominio de los conjuntos del problema.
    Variables:
        -n_ex : Número de procesos de extracción (int).
        -n_tec: Número de tipos de tecnología (int).
        -t_mes: Horizonte de tiempo del problema, en meses (int).
        -n_pl : Número de plantas de extracción de agua (int).
        -n_m  : Número de métodos de transporte de agua (int). 
        -n    : Nombre del modelo (str). Default: V1. 
    Retorna una tupla compuesta por un modelo m con nombre n y la 
    función objetivo. (m, obj). 
    """
    m = gp.Model(name=n)
    seed(20)
    np.random.seed(20)
    ### Conjuntos ###
    
    # Procesos de extracción i in {1, ..., I}
    I = range(n_ex)
    # Tipo de tecnología h in {1, ..., H}
    H = range(n_tec)
    # Mes transcurrido t in {1, ..., T}
    T = range(t_mes)
    # Plantas para extraer agua p in {1, ..., P}
    P = range(n_pl)
    # Métodos para transportar el agua planta->salar m in {1, ..., M}
    M = range(n_m)
    
    ### Parámetros ###
    
    # Costo de extraer 1000L de agua de la planta p:
    c_ag    = [np.random.normal(16507867, 16507867 * 0.05) for p in P]
    # Costo de transportar 1000L de agua desde la planta p hasta el salar.
    # Medido en PESOS CHILENOS
    c_tr_list = [4089730, 2048309, 1790602, 1738501, 6438591]
    c_tr    = {(p, m): randint(50, 500) * 1.1 * precio for p in P for m, precio in enumerate(c_tr_list)}
    # Costo de adquisición de la tecnología h para el proceso i
    # Medido en PESOS CHILENOS
    costo_proc = [26616344, 71784659, 88113078]
    num = [randint(1, n_tec) for i in range(3)]
    c       = {(i, h): np.random.normal(proceso, proceso * 0.05) if num[i] >= np.max(num) else costo_proc[i] for i, proceso in enumerate(costo_proc) for h in range(np.max(num))}
    # Costo de usar el proceso i con la tecnología h en el tiempo t
    # Medido en PESOS CHILENOS POR GRAMO DE LITIO
    costo_aux = [2000000, 67052421 + 36591183, 67052421 + 36591183]
    ct      = {(i, h, t): valor for i, valor in enumerate(costo_aux) for h in H for t in T}
    # Cantidad máxima de agua que se puede extraer de la planta p en un mes
    # medido en LITROS
    cmax_ag = [np.random.normal(200000, 200000 * 0.05) for p in P]
    # Cantidad de agua mínima que requiere la tecnología h para el proceso i.
    # medido en LITROS
    valores = [10000, 10000, 100000]
    tech_ag = {(i, h): np.random.normal(proceso, proceso * 0.05) if num[i] >= np.max(num) else valores[i] for i, proceso in enumerate(valores) for h in range(np.max(num))}
    # Cantidad de agua que se retorna al salar al terminar el proceso con
    # la tecnología h en el tiempo t.
    # medido en LITROS
    ret_ag  = {(i, h, t): np.random.normal(100000) for i in I for h in H for t in T}
    # Cantidad de carbonato de litio que produce el proceso i con la tecnología h
    # medido en TONELADAS DE LiCO3
    valor_proceso = [78182*0.15, 78182*0.15, 78182*0.7]
    cl      = {(i, h): np.random.normal(valor, valor*0.05) for i, valor in enumerate(valor_proceso) for h in H}
    # Huella ambiental del proceso i con la tecnología h
    # medido en KILOGRAMOS (de CO2) POR TONELADA DE CARBONATO DE LITIO
    ha      = {(i, h): np.random.normal(4022, 4022*0.05) for i in I for h in H}
    # Huella ambiental máxima que puedo liberar al terminar el horizonte de tiempo.
    # medido en KILOGRAMOS (de CO2) POR TONELADA DE CARBONATO DE LITIO
    ha_max  = 6650 * t_mes
    # Demanda total del litio al fin del horizonte de tiempo
    # medido en TONELADAS
    dt      = 343981 + 5034
    # Tiempo que demora una iteración del proceso i en estar listo con la tecnología h.
    # medido en MESES
    a       = {(i, h): randint(12, 18) for i in I for h in H}
    # Orden de procesos, 1 si el proceso i debe ocurrir antes del proceso j
    order   = {(i, j): 1 if i < j else 0 for i in I for j in I}
    
    ### Variables ###
    
    # Estas variables son continuas
    
    # Cantidad de agua que saco de la planta p en el mes t
    q_ag   = m.addVars(P, T, name='Cantidad de agua de planta')
    # Cantidad de agua que saco del salar al final del horizonte de tiempo
    q_ag_s = m.addVar(name='Cantidad de agua retirada')
    # tiempo en que se inicia el proceso i con la tecnología h
    start  = m.addVars(I, H, name='Instante de inicio del proceso')
    
    # Estas variables son 1 si cumplen con su descripción, 0 en otro caso.
    
    # Variable binaria que indica si uso el proceso i con la tecnología h.
    x = m.addVars(I, H, vtype=gp.GRB.BINARY, name='Compra de tecnologia')
    # Variable binaria que indica si uso el proceso i con la tecnología h
    # en el mes t.
    y = m.addVars(I, H, T, vtype=gp.GRB.BINARY, name='Uso de tecnologia en el mes')
    # Variable binaria que indica si uso el transporte m para agua de la planta p
    z = m.addVars(P, M, vtype=gp.GRB.BINARY, name='Uso de transporte de agua')
    # Variable binaria que indica si el proceso i es utilizado
    w = m.addVars(I, vtype=gp.GRB.BINARY, name='Uso proceso en algun caso')
    ### Restricciones ###
    m.update()
    
    # R1: No superar la cantidad máxima de agua que puedo extraer de una planta.
    m.addConstrs(q_ag[p, t] <= cmax_ag[p] for p in P for t in T)
    # R2: Agua sacada del salar debe ser la misma que la retornada en el horizonte de tiempo:
    m.addConstr(gp.quicksum(y[i, h, t] * ret_ag[i, h, t] for i in I for h in H for t in T) - q_ag_s >= 0)
    # R3: No superar cota ambiental de contaminación
    m.addConstr(ha_max - gp.quicksum(y[i, h ,t] * ha[i, h] for i in I for h in H for t in T) >= 0)
    # R4: Suplir la demanda de Litio
    m.addConstr(dt - gp.quicksum(y[i, h, t] * cl[i, h] for i in I for h in H for t in T) <= 0)
    # R5: Tener requerimiento mínimo de agua para cada proceso i con tecnología h
    m.addConstr(q_ag_s + gp.quicksum(q_ag[p, t] for p in P for t in T) 
                 >= gp.quicksum(y[i, h, t] * tech_ag[i, h] for i in I for h in H for t in T))
    # R6: Mantener secuencialidad de los procesos:
#     m.addConstrs(start[i, h] <= (start[j, h] + x[j, h] * a[j, h]) \
#                  * order[i, j] for h in H for i in I for j in I if i != j)
    # R7: Un proceso solo puede ocupar una tecnología a la vez
    m.addConstrs(gp.quicksum(y[i, h, t] for h in H) <= 1 for i in I for t in T)
    # R8: Se realiza un proceso a la vez
    m.addConstrs(gp.quicksum(y[i, h, t] for i in I for h in H) <= 1 for t in T)
    # R9: Relación entre blabla ver informe
    m.addConstrs(gp.quicksum(y[i, h, t] for t in T) <= 500000 * x[i, h] for i in I for h in H)
    m.addConstrs(gp.quicksum(y[i, h, t] for t in T) >= x[i, h] for i in I for h in H)
    # R10: el retorno de agua tiene que ser igual al agua sacada de las plantas menos el agua utilizada por los procesos
    m.addConstrs(gp.quicksum(q_ag[p, t] - tech_ag[i, h] - ret_ag[i, h, t] for p in P for i in I for h in H) >= 0 for t in T)
    # R11: se deben ocupar al menos dos procesos
    m.addConstr(gp.quicksum(w[i] for i in I) >= 2)
    m.addConstrs(gp.quicksum(x[i, h] for h in H) == w[i] for i in I)
    # R12: 
#   m.addConstrs(start[i, h] - start [j, h] >= 1  for i in I for j in I for h in H if i < j)
    # Naturaleza de las variables:
    m.addConstr(q_ag_s >= 0)
    m.addConstrs(q_ag[p, t] >= 0 for p in P for t in T)
    m.addConstrs(start[i, h] >= 0  for i in I for h in H)
    
    ### Función objetivo ###
    
    costo_agua = gp.quicksum(q_ag[p, t] * c_ag[p] for p in P for t in T) \
                 + gp.quicksum(z[p, m] * c_tr[p, m] for p in P for m in M)
    costo_tec  = gp.quicksum(x[i, h] * c[i, h] for i in I for h in H) \
                 + gp.quicksum(y[i, h, t] * ct[i, h, t] for i in I for h in H for t in T)
    obj = costo_agua + costo_tec
    
    return m, obj
  
