import gurobipy as gp
from random import randint, choices, seed


def modelador(n_ex, n_tec, t_mes, n_pl, n_m, n='V1'):
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
    # archivo parametros Cote:
    # https://docs.google.com/document/d/16tpIgbT18wJ0YU0W5X2hlRgIwC1qytQKJiMMTKI5OdM/edit?usp=sharing
    # (Es una copia, no el original por lo que podría no estar actualizado)
    # Costo de extraer 1000L de agua de la planta p:
    # No se en que moneda está el valor 16507867 -Diego
    c_ag    = [16507867 for p in P]
    # Costo de transportar 1000L de agua desde la planta p hasta el salar.
    # Los valores están en la misma moneda que el parámetro anterior
    # tome el valor mas alto y el mas bajo de entre los 5 valores para generar los numeros
    c_tr    = {(p, m): randint(1738501, 6438591) for p in P for m in M}
    # Costo de adquisición de la tecnología h para el proceso i
    # No entendí la tabla del doc, asique dejé esta linea tal como estaba
    c       = {(i, h): randint(500, 1000) for i in I for h in H}
    # Costo de usar el proceso i con la tecnología h en el tiempo t
    # No entendí la tabla del doc, asique dejé esta linea tal como estaba
    ct      = {(i, h, t): choices([0, 1], [.7, .3])[0] for i in I for h in H for t in T}
    # Cantidad máxima de agua que se puede extraer de la planta p en un mes
    # medido en LITROS
    cmax_ag = [100000 for p in P]
    # Cantidad de agua mínima que requiere la tecnología h para el proceso i.
    # No está especificado, asique dejé esta linea tal como estaba
    tech_ag = {(i, h): 700 for i in I for h in H}
    # Cantidad de agua que se retorna al salar al terminar el proceso con
    # la tecnología h en el tiempo t.
    # medido en LITROS
    ret_ag  = {(i, h, t): randint(0, 4780000000) for i in I for h in H for t in T}
    # Cantidad de carbonato de litio que produce el proceso i con la tecnología h
    # medido en TONELADAS
    cl      = {(i, h): randint(1775, 78182) for i in I for h in H}
    # Huella ambiental del proceso i con la tecnología h
    # medido en KILOGRAMOS (de CO2) POR TONELADA DE CARBONATO DE LITIO
    ha      = {(i, h): 4022 for i in I for h in H}
    # Huella ambiental máxima que puedo liberar al terminar el horizonte de tiempo.
    # medido en KILOGRAMOS (de CO2) POR TONELADA DE CARBONATO DE LITIO
    ha_max  = 6650 * t_mes
    # Demanda total del litio al fin del horizonte de tiempo
    # medido en TONELADAS
    dt      = 323000
    # Tiempo que demora una iteración del proceso i en estar listo con la tecnología h.
    # medido en MESES
    a       = [randint(12, 18) for i in I for h in H]
    # Orden de procesos, 1 si el proceso i debe ocurrir antes del proceso j
    order   = {(i, j): choices([0, 1], [.7, .3])[0] for i in I for j in I if i != j}
    
    ### Variables ###
    
    # Estas variables son continuas
    
    # Cantidad de agua que saco de la planta p en el mes t
    q_ag   = m.addVars(P, T, name='Cantidad de agua de planta')
    # Cantidad de agua que saco del salar al final del horizonte de tiempo
    q_ag_s = m.addVar(name='Cantidad de agua retirada')
    # Mes en que se inicia el proceso i con la tecnología h
    start  = m.addVars(I, H, name='Instante de inicio del proceso')
    
    # Estas variables son 1 si cumplen con su descripción, 0 en otro caso.
    
    # Variable binaria que indica si uso el proceso i con la tecnología h.
    x = m.addVars(I, H, vtype=gp.GRB.BINARY, name='Compra de tecnologia')
    # Variable binaria que indica si uso el proceso i con la tecnología h
    # en el mes t.
    y = m.addVars(I, H, T, vtype=gp.GRB.BINARY, name='Uso de tecnologia en el mes')
    # Variable binaria que indica si uso el transporte m para agua de la planta p
    z = m.addVars(P, M, vtype=gp.GRB.BINARY, name='Uso de transporte de agua')
    
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
#     m.addConstrs(start[i, h] <= (start[j, h] + gp.quicksum(x[j, h] * a[j, h] for h in H)) \
#                  * order[i, j] for i in I for for j in I)
    # R7: Un proceso solo puede ocupar una tecnología a la vez
    m.addConstrs(gp.quicksum(y[i, h, t] for h in H) <= 1 for i in I for t in T)
    # R8: Se realiza un proceso a la vez
    m.addConstrs(gp.quicksum(y[i, h, t] for i in I for h in H) <= 1 for t in T)
    # R9: Relación entre blabla ver informe
    m.addConstrs(gp.quicksum(y[i, h, t] for t in T) <= 500000 * x[i, h] for i in I for h in H)
    m.addConstrs(gp.quicksum(y[i, h, t] for t in T) >= x[i, h] for i in I for h in H)
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
  
