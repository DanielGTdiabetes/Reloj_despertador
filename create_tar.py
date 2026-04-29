import tarfile, os
os.chdir('D:/Reloj_despertador')
t = tarfile.open('project.tar', 'w')
for f in ['config', 'src']:
    t.add(f)
t.close()
print('TAR_OK')
