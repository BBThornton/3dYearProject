# import format_input
import os
import subprocess
import re


file_location = "./data/morgan/freq_tab_json/out_freq_table.tsv"
out_location = "./data/morgan/lefse"

with open(out_location+"/in.txt",'w') as filtered:
    with open(file_location) as f:
        for line in f:
            new_line = line.replace(";","|")
            # new_line = new_line.replace("UC","IBD")
            # new_line = new_line.replace("CD","IBD")
            new_line = new_line.replace("|____","")
            new_line = re.sub('\\|__+', '', new_line)
            new_line = re.sub('\\|g__\t', '\t', new_line)
            new_line = re.sub('\\|f__\t+', '\t', new_line)
            filtered.writelines(new_line)
filtered.close()
f.close()

subprocess.call(['format_input.py',out_location+"/in.txt",out_location+'/data.in','-c','1','-u','2','-o','1000000000'])
subprocess.call(['run_lefse.py', out_location+'/data.in', out_location+'/lefse_data.res','--wilc','0'])
subprocess.call(['plot_res.py',out_location+'/lefse_data.res', out_location+'/lefse_chart.png'])
subprocess.call(['plot_cladogram.py',out_location+'/lefse_data.res', out_location+'/lefse_cladogram.svg','--format','svg'])
# subprocess.call(['plot_cladogram.py','--help'])