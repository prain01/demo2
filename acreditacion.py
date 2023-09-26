import pandas as pd

# Segun el tipo_matricula, da resultados totales o nuevos por año
def matricula(codigos_carrera, sede, años, foto_sies_2013_2023, tipo_matricula):
    sies = foto_sies_2013_2023.copy()

    # Filtrar por pregrado, años, códigos de carrera, sede y matrícula nueva
    sies = sies[(sies['MC_NIVEL_GLOBAL'] == 'Pregrado') &
                (sies['MM_ANIO_ORIGEN'].isin(años)) & 
                (sies['cod_carrer.x'].isin(codigos_carrera)) & 
                (sies['MC_NOMB_SEDE'].isin(sede))]

    if tipo_matricula == 'Nueva':
        sies = sies[sies['Mat_nueva'] == True]
    elif tipo_matricula == 'Total':
        pass

    df =  sies.groupby(['MM_ANIO_ORIGEN', 'Admisión'])['MM_SEXO'].value_counts().unstack(fill_value=0)
    df['Total'] = df['H'] + df['M']
    df['Porcentaje_mujeres'] = (df['M'] / df['Total']).round(3)
    df = df.sort_values(by=['MM_ANIO_ORIGEN', 'Admisión'], ascending=[True, False]).reset_index()
    
    df_años = df['MM_ANIO_ORIGEN'].unique()
    años = [año for año in años if año in df_años]

    df_pivot = df.pivot(index='Admisión', columns='MM_ANIO_ORIGEN', values=['Total', 'Porcentaje_mujeres'])
    df_pivot.columns = [f"{col[1]}_{col[0]}" for col in df_pivot.columns]
    df_pivot = df_pivot.reset_index()
    df_pivot = df_pivot.rename(columns={'Admisión': 'Tipo'})
    df_pivot = df_pivot.reindex(index=df_pivot.index[::-1])

    nuevas_columnas = []
    for año in años:
        nuevas_columnas.extend([f'{año}_Total', f'{año}_Porcentaje_mujeres'])
    nuevas_columnas = ['Tipo'] + nuevas_columnas
    
    columnas_existentes = [col for col in nuevas_columnas if col in df_pivot.columns]
    df_pivot = df_pivot[columnas_existentes]

    if df_pivot[df_pivot['Tipo'] == 'Especial'].empty:
        df_pivot.loc[len(df_pivot)] = ['Especial'] + [0] * (len(df_pivot.columns) - 1)
    df_pivot.loc[len(df_pivot)] = ['Otro'] + [0] * (len(df_pivot.columns) - 1)
    df_pivot = df_pivot.fillna(0)

    total_año = pd.DataFrame(columns=['Año', 'Total', 'Porcentaje_mujeres'])
    for año in años:
        total_regular = df_pivot.loc[df_pivot['Tipo'] == 'Regular'][f'{año}_Total'].values[0]
        total_especial = df_pivot.loc[df_pivot['Tipo'] == 'Especial', f'{año}_Total'].values[0] if not df_pivot[df_pivot['Tipo'] == 'Especial'].empty else 0
        total = total_regular + total_especial

        total_regular_mujeres = df_pivot.loc[df_pivot['Tipo'] == 'Regular'][f'{año}_Porcentaje_mujeres'].values[0] * total_regular
        total_especial_mujeres = (df_pivot.loc[df_pivot['Tipo'] == 'Especial', f'{año}_Porcentaje_mujeres'].values[0] * total_especial) if not df_pivot[df_pivot['Tipo'] == 'Especial'].empty else 0

        porcentaje_mujeres = (total_regular_mujeres + total_especial_mujeres) / total
        total_año = pd.concat([total_año, pd.DataFrame({'Año': año, 'Total': total, 'Porcentaje_mujeres': porcentaje_mujeres}, index=[0])], ignore_index=True)

    total_año_tmp = pd.DataFrame(columns=[])
    for año in años:
        total_año_tmp[f'{año}_Total'] = [total_año[total_año['Año'] == año]['Total'].values[0]]
        total_año_tmp[f'{año}_Porcentaje_mujeres'] = [total_año[total_año['Año'] == año]['Porcentaje_mujeres'].values[0]]
    
    df_final = pd.concat([df_pivot, total_año_tmp], ignore_index=True)
    df_final.iloc[-1, 0] = 'Total'
    

    return {'Matricula Nueva': df_final.to_string(index=False)} if tipo_matricula == 'Nueva' else {'Matricula Total': df_final.to_string(index=False)}


def tasa_ocupacion(codigos_carrera, sede, años, oferta_pregrado):
    df = oferta_pregrado.copy()

    df = df[(df['AÑO'].isin(años) &
             df['CÓDIGO.UFRO'].isin(codigos_carrera) &
             df['NOMBRE SEDE'].isin(sede))]

    df = df[['NOMBRE SEDE', 'CÓDIGO.UFRO', 'AÑO', 'Vacantes', 'Admisión Regular', 'Admisión Especial']]
    df['Regular'] = df.apply(lambda row: row['Admisión Regular'] / row['Vacantes'] if row['Vacantes'] != 0 else 0, axis=1)
    df['Especial'] = df.apply(lambda row: row['Admisión Especial'] / row['Vacantes'] if row['Vacantes'] != 0 else 0, axis=1)

    df_pivot = df.pivot_table(columns='AÑO', values=['Regular', 'Especial'])
    df_pivot.index.name = None
    df_pivot = df_pivot.reindex(index=df_pivot.index[::-1])
    df_pivot.loc['Total'] = df_pivot.sum()

    return { 'Tasa Ocupacion': df_pivot }


def puntajes_promedio(codigos_carrera, sede, años, foto_sies_2013_2023):
    sies = foto_sies_2013_2023.copy()

    sies = sies[(sies['MC_NIVEL_GLOBAL'] == "Pregrado") &
                (sies['MM_ANIO_ORIGEN'].isin(años)) &
                (sies['MC_NOMB_SEDE'].isin(sede)) &
                (sies['cod_carrer.x'].isin(codigos_carrera))]
    
    df = sies[(sies['Mat_nueva'] == True) & (sies['Admisión'] == 'Regular')]

    df_prom = df.groupby(['MC_NOMB_SEDE', 'MM_ANIO_ORIGEN', 'MM_SEXO'])[['paa_promed', 'paes_prom']].mean().unstack(fill_value=0)
    df_sexo = df.groupby(['MC_NOMB_SEDE', 'MM_ANIO_ORIGEN'])['MM_SEXO'].value_counts().unstack(fill_value=0)
    df_prom = df_prom.fillna(0)

    df_sexo['H'] = 0 if 'H' not in df_sexo.columns else df_sexo['H']
    df_sexo['M'] = 0 if 'M' not in df_sexo.columns else df_sexo['M']

    df_sexo['Total'] = df_sexo['H'] + df_sexo['M']
    df_prom[['H', 'M', 'Total']] = df_sexo[['H', 'M', 'Total']].values
    df_prom = df_prom.reset_index()

    desired_multiindex = pd.MultiIndex.from_tuples([
        ('MC_NOMB_SEDE', ''),
        ('MM_ANIO_ORIGEN', ''),
        ('paa_promed', 'H'),
        ('paa_promed', 'M'),
        ('paes_prom', 'H'),
        ('paes_prom', 'M'),
        ('H', ''),
        ('M', ''),
        ('Total', '')
    ], names=[None, 'MM_SEXO'])

    df_prom = df_prom.reindex(columns=desired_multiindex, fill_value=0)
    df_prom.columns = ['MC_NOMB_SEDE', 'MM_ANIO_ORIGEN', 'H_paa', 'M_paa', 'H_pae', 'M_pae', 'H', 'M', 'Total']

    df_prom['T_paa'] = (df_prom['H_paa'] * df_prom['H'] + df_prom['M_paa'] * df_prom['M']) / df_prom['Total']
    df_prom['T_pae'] = (df_prom['H_pae'] * df_prom['H'] + df_prom['M_pae'] * df_prom['M']) / df_prom['Total']

    df_paa = df_prom[['MM_ANIO_ORIGEN', 'M_paa', 'H_paa', 'T_paa']]
    df_pae = df_prom[['MM_ANIO_ORIGEN', 'M_pae', 'H_pae', 'T_pae']]    

    df_paa = df_paa.set_index('MM_ANIO_ORIGEN').T.round(2)
    df_pae = df_pae.set_index('MM_ANIO_ORIGEN').T.round(2)

    for año in años:
        if año not in df_paa.columns:
            df_paa[año] = 0
        if año not in df_pae.columns:
            df_pae[año] = 0

    df_final = pd.concat([df_paa, df_pae])
    df_final = df_final[[año for año in años]]
    
    return { 'Puntajes Promedio': df_final }


def retencion(codigos_carrera, sede, años, foto_sies_2013_2023, tipo_retencion):
    sies = foto_sies_2013_2023.copy()

    sies = sies[(sies['MC_NIVEL_GLOBAL'] == "Pregrado") &
                (sies['MM_ANIO_ORIGEN'].isin(años)) &
                (sies['MC_NOMB_SEDE'].isin(sede)) &
                (sies['cod_carrer.x'].isin(codigos_carrera))]
    
    df_estudiantes = sies[['matricula', 'Año', 'MM_ANIO_ORIGEN', 'MM_SEXO']]
    df_estudiantes['Condición'] = 'Otro'
    condiciones = ['Matricula 1er Año', 'Retencion 1er Año', 'Retencion 2do año', 'Retencion 3er Año', 'Retencion 4to año', 'Retencion 5to año']

    for i, condicion in enumerate(condiciones):
        df_estudiantes.loc[(df_estudiantes['Año'] - df_estudiantes['MM_ANIO_ORIGEN'] == i), 'Condición'] = condicion

    df_retencion = pd.DataFrame(columns=['Año', 'M', 'H', 'Total', 'Porcentaje Hombre', 'Porcentaje Mujer', 'Porcentaje Total'])
    df_matricula = pd.DataFrame(columns=['Año', 'M', 'H', 'Total'])
    for año in años:
        
        if tipo_retencion == 'Retencion 1er Año':
            año_mat = año - 1
        else:
            año = año + 3
            año_mat = año - 3

        año_ret = año

        if año_mat < años[0]:
            continue
        
        if tipo_retencion == 'Retencion 1er Año':
            df_mat_tmp = df_estudiantes[(df_estudiantes['Condición'] == 'Matricula 1er Año') & (df_estudiantes['MM_ANIO_ORIGEN'] == (año_mat))]
            df_ret_tmp = df_estudiantes[(df_estudiantes['Condición'] == 'Retencion 1er Año') & (df_estudiantes['Año'] == año_ret)]
        elif tipo_retencion == 'Retencion 3er Año':
            df_mat_tmp = df_estudiantes[(df_estudiantes['Condición'] == 'Matricula 1er Año') & (df_estudiantes['MM_ANIO_ORIGEN'] == (año_mat))]
            df_ret_tmp = df_estudiantes[(df_estudiantes['Condición'] == 'Retencion 3er Año') & (df_estudiantes['Año'] == año_ret)]


        matriculas_interseccion = set(df_mat_tmp['matricula']) & set(df_ret_tmp['matricula'])
        df_ret = df_mat_tmp[df_mat_tmp['matricula'].isin(matriculas_interseccion)]

        total_mat_hombre = len(df_mat_tmp[df_mat_tmp['MM_SEXO'] == 'H'])
        total_mat_mujer = len(df_mat_tmp[df_mat_tmp['MM_SEXO'] == 'M'])
        total_mat = total_mat_hombre + total_mat_mujer
        df_mat_tmp = pd.DataFrame({'Año': [año_mat], 'M': [total_mat_mujer], 'H': [total_mat_hombre], 'Total': [total_mat]})
        df_matricula = pd.concat([df_matricula, df_mat_tmp], ignore_index=True)
            
        total_ret_hombre = len(df_ret[df_ret['MM_SEXO'] == 'H'])
        total_ret_mujer = len(df_ret[df_ret['MM_SEXO'] == 'M'])
        total_ret = total_ret_hombre + total_ret_mujer

        porcentaje_ret_hombre = (total_ret_hombre / total_mat_hombre) if total_mat_hombre > 0 else 0
        porcentaje_ret_mujer = (total_ret_mujer / total_mat_mujer) if total_mat_mujer > 0 else 0
        porcentaje_total = (total_ret / total_mat) if total_mat > 0 else 0

        df_ret_tmp = pd.DataFrame({'Año': [año_mat], 'M': [total_ret_mujer], 'H': [total_ret_hombre], 'Total': [total_ret], 'Porcentaje Hombre': [porcentaje_ret_hombre], 'Porcentaje Mujer': [porcentaje_ret_mujer], 'Porcentaje Total': [porcentaje_total]})
        df_retencion = pd.concat([df_retencion, df_ret_tmp])

    df_retencion = df_retencion[['Año', 'Porcentaje Mujer', 'Porcentaje Hombre', 'Porcentaje Total']]
    df_retencion = df_retencion.set_index('Año')
    df_retencion = df_retencion.T
    if tipo_retencion == 'Retencion 3er Año':
        # Considerar solo de 2016 a 2020
        df_retencion = df_retencion[[2016, 2017, 2018, 2019, 2020]]
    # print(df_retencion)
    return ({'Retencion 1er Año': df_retencion}) if tipo_retencion == 'Retencion 1er Año' else ({'Retencion 3er Año': df_retencion})