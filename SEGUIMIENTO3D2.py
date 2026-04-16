from machine import ADC, Pin  # importacion de las librerias para usar el codigo
import time #importacion del tiempo

# declaracion del pin para el sensor 
sensor = ADC(Pin(34)) # sensor en el pin 34 y es ADC para analogo-digital
sensor.atten(ADC.ATTN_11DB) # permite ajustar el rango de voltaje a 0 - 3.3V para leerlo
sensor.width(ADC.WIDTH_12BIT) #resolucion de 12bits va desde 0 hasta 4095

# declaracion del led que indica que la señal se esta recopilando o leyendo
led = Pin(2, Pin.OUT)

# declaracion de los leds para ver visualmente que los filtros funcionan
# cada led pertenece a un filtro
led_prom = Pin(25, Pin.OUT)
led_med  = Pin(26, Pin.OUT)
led_exp  = Pin(33, Pin.OUT)

# declaracion de los botones oara activar y desactivar los filtros  # los botones estan en 1
btn_prom = Pin(12, Pin.IN, Pin.PULL_UP) # boton filtro promedio
btn_med  = Pin(14, Pin.IN, Pin.PULL_UP) # boton filtro mediana
btn_exp  = Pin(27, Pin.IN, Pin.PULL_UP) # boton filtro exponencial

# declaracion del boton para modificar la frecuencia
btn_freq = Pin(13, Pin.IN, Pin.PULL_UP)

# declaracion de las variables principales del codigo 
frecuencia = 50 #frecuencia de muestreo (que tan rapido va la grafica)
dt = 1 / frecuencia  #tiempo en el que se toman las muestras

# indican en que estado estan los filtros (Activos o inactivos)
usar_prom = True
usar_med = True
usar_exp = True

# anti rebote sirve para detectar los estados de los botones
prev_prom = 1
prev_med = 1
prev_exp = 1
prev_freq = 1

# filtros
N = 10 #define cuantas muestras vamos a tomar (10 ultimos datos del sensor)
buffer = [0] * N # crea una lista de tamaño N donde se guardan los datos
index = 0 #indica la posicion en la que tienen que ir los datos hace el bucle de los datos

alpha = 0.2 # para decir cuanto pesan los datos que se recopilan y que tan fuerte es el filtro
filtro_exp = 0 # es la memoria del filtro exponencial

# Archivos aqui declaramos los archivos que vamos a guardar 
file_txt = open("/marga3.txt", "a") #memoria interna del esp32
file_csv = open("/marga3.csv", "a") #para ver en excel

file_csv.write("crudo,prom,med,filtrado\n") # asi van a estar nombradas las columnas del excel
file_csv.flush()

print("=== SISTEMA INICIADO ===") # mensaje que sale en el shell o consola al iniciar

# bucle principal
while True:

    # se leen los estados de los botones para saber como estan los filtros
    act_prom = btn_prom.value()
    act_med  = btn_med.value()
    act_exp  = btn_exp.value()
    act_freq = btn_freq.value()

    # detecta cuando se accionan los botones y le da ON/OFF a los filtros
    if prev_prom == 1 and act_prom == 0: #detecta los estados
        usar_prom = not usar_prom # segun como este el estado activa el filtro
        print("Promedio:", usar_prom) #imrpime el estado del filtro

    if prev_med == 1 and act_med == 0:
        usar_med = not usar_med
        print("Mediana:", usar_med)

    if prev_exp == 1 and act_exp == 0:
        usar_exp = not usar_exp
        print("Exponencial:", usar_exp)

    # frecuencia a la cual se va a iniciar en este caso 50
    if prev_freq == 1 and act_freq == 0:
        frecuencia += 50
# declaramos que la frecuencia va a aumentar de 50 en 50 y que al llegar a 500 vuelve a 50
        if frecuencia > 500:
            frecuencia = 50

        dt = 1 / frecuencia  # va actualizando el tiempo de muestreo
        print("Frecuencia:", frecuencia, "Hz") #imprime en cuanto esta la frecuencia 


# actualiza los estados de los filtros y los de los leds
    prev_prom = act_prom
    prev_med = act_med
    prev_exp = act_exp
    prev_freq = act_freq

    led_prom.value(usar_prom)
    led_med.value(usar_med)
    led_exp.value(usar_exp)

    # lee los valores del sensor de 0 a 4095
    valor = sensor.read()

    buffer[index] = valor # guarda los datos en el buffer en los filtros
    index = (index + 1) % N # hace que despues de que se guarden los datos vuelve a empezar

    # Filtros en cascada
    #filtro promedio
    prom = sum(buffer) / N if usar_prom else valor #saca el promedio de los 10 ultimos digitos
 # filtro mediana , ordena los valores y toma el valor del medio
    temp = sorted(buffer)
    med = temp[N // 2] if usar_med else prom
# filtro exponencial
#toma los datos anteriores y los mezcla con los nuevos y suaviza la onda
    if usar_exp:
        filtro_exp = alpha * med + (1 - alpha) * filtro_exp
    else:
        filtro_exp = med

    salida = filtro_exp #filtro final en cascada con los 3 filtros

    # indicacion de la lectura del led
    led.value(1)
    time.sleep(0.002)
    led.value(0)

    # en este paso podemos imprimir las dos señales en esta caso la cruda que es valor
    # y la filtrada que es salida
    print(valor, salida)

    # Guardamos en txt y csv
    # se crean unas listas en las que se alamacenan las variables
    file_txt.write("{},{},{},{}\n".format(valor, prom, med, salida))
    file_csv.write("{},{},{},{}\n".format(valor, prom, med, salida))

    file_txt.flush() # permite guardar la informacion
    file_csv.flush()

    # tiempo como el time hardware
    time.sleep(dt)  #(controla la frecuencia de muestreo)