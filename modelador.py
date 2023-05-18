import gurobipy as gp
from random import randint, choices

def modelador(n_ex, n_tec, t_mes, n='V1'):
    """Función que define el dominio de los conjuntos del problema.
    Variables:
        -n_ex : Número de procesos de extracción (int).
        -n_tec: Número de tipos de tecnología (int).
        -t_mes: Horizonte de tiempo del problema, en meses (int).
        -n    : Nombre del modelo (str). Default: V1. 
    Retorna un modelo m con nombre n. 
    """
    m = gp.Model(n)
    
    ### Conjuntos ###
    
    # Procesos de extracción i in {1, ..., I}
    I = range(n_ex)
    # Tipo de tecnología h in {1, ..., H}
    H = range(n_tec)
    # Mes transcurrido t in {1, ..., T}
    T = range(t_mes)
    
    ### Parámetros ###

    # Costo de implementar un proceso en la extracción de Litio que depende
    # del proceso i según la tecnología h aplicada.
    c  = {(i, h): randint(500, 1000) for i in I for h in H}
    # Costo de mantención del proceso i segun la tecnología h aplicada en 
    # el tiempo t
    ct = {(i, h, t): choices([0, 1], [.7, .3])[0] for i in I for h in H for t in T}
    # Toneladas de carbonato de litio que produce el proceso i
    cl = [randint(4000, 5000) for i in I]
    # Cantidad de agua que ocupa cada proceso i que depende de la tecnología
    # h en el mes t
    q  = {(i, h, t): randint(1000, 2000) for i in I for h in H for t in T}
    # Tiempo que demora una iteración del proceso i en estar listo
    a  = [randint(5, 24) for i in I]
    # Huella ambiental del proceso i con la tecnología h
    ha = {(i,h): randint(0, 1000) for i in I for h in H}
    # Demanda total del litio en el mes t
    dt = [randint(4000, 40000) for t in T]
    # Cantidad de agua que se retorna al ambiente al terminar el proceso
    # usando la tecnología h
    cr = {(i, h, t): randint(0, 1000) for i in I for h in H for t in T}
    # Margen de utilidades en el horizonte de tiempo
    u  = 500000
    # Precio de una tonelada de carbonato de litio en el mes t
    pl = [randint(1000, 10000) for t in T]
    # Límite ambiental de contaminación que se permite por mes
    la = 500000
    
    ### Variables ###
    # Estás variables son 1 si cumplen con su descripción, 0 en otro caso.
    
    # Variable binaria que indica si uso el proceso i con la tecnología h.
    x = m.addVars(I, H, vtype=gp.GRB.BINARY, name='x')
    # Variable binaria que indica si uso el proceso i con la tecnología h
    # en el mes t.
    y = m.addVars(I, H, T, vtype=gp.GRB.BINARY, name='y')
    # Variable binaria que indica si el proceso i termina en el mes t.
    z = m.addVars(I, T, vtype=gp.GRB.BINARY, name='z')
    # Variable binaria que indica si el proceso i inicia en el mes t.
    v = m.addVars(I, T, vtype=gp.GRB.BINARY, name='v')
    
    ### Restricciones ###
    
    # R1: Mantener o incrementar utilidades.
    m.addConstrs(gp.quicksum(cl[i] * pl[t] * y[i, h, t] - \
                          (c[i, h] * x[i, h] + ct[i, h, t] * y[i, h, t]) 
                          for i in I for h in H) 
                          >= u  for t in T)
    # R2: Suplir la demanda cuando el proceso i termina.
    m.addConstrs(gp.quicksum(cl[i] * y[i, h, t] for i in I for h in H)
                 >= dt[t] * gp.quicksum(z[k, t] for k in I) for t in T)
    # R3: No superar cota ambiental de contaminación
    m.addConstrs(gp.quicksum(ha[i, h] * y[i, h, t] for i in I for h in H)
                 <= la  for t in T)
    # R4: No se puede aplicar más de una tecnología h en un mismo proceso i
    m.addConstrs(gp.quicksum(y[i, h, t] for h in H) 
                 <= 1 for i in I for t in T)
    # R5: Tiempo de producción no puedo superar el horizonte de tiempo.
    m.addConstrs(gp.quicksum(z[i, t] * a[i] for t in T) 
                 <= t_mes for i in I for h in H)
    # R6: De usar más de un proceso en el horizonte de tiempo, no puede
    # ocurrir el proceso i1 despues del proceso i2.
    m.addConstrs(y[i, h, t + 1]
                 <= 50000000 * (1 - y[k, h, t]) \
                 for t in range(t_mes -1) for h in H for i in I for k in I if i < k)
    # R7: La ocurrencia de Y activa a X si la suma de los Y en todo el tiempo
    # es cero, entonces X será cero.
    m.addConstrs(gp.quicksum(y[i, h, t] for t in T) 
                 <= 50000000 * x[i, h] for i in I for h in H)
    # R8: El proceso i tiene que durar el tiempo que demora su iteración
    m.addConstrs(v[i, t] 
                 == z[i, t + a[i]] for i in I for t in T if t + a[i] < t_mes)
    
    ### Función objetivo ###
    obj = gp.quicksum((q[i, h, t] - cr[i, h, t]) * y[i, h, t] \
                 for i in I for h in H for t in T)
    
    return m, obj
  