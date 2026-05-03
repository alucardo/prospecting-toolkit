from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0056_brandprofile_extra_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandprofile',
            name='archetype',
            field=models.CharField(
                max_length=50,
                blank=True,
                verbose_name='Archetyp marki',
                choices=[
                    ('innocent', 'Niewinny — szczęście, optymizm, prostota'),
                    ('sage', 'Mędrzec — zrozumienie, wiedza, prawda'),
                    ('explorer', 'Odkrywca — autonomia, wolność, przygoda'),
                    ('outlaw', 'Buntownik — wolność, rewolucja, zmiana zasad'),
                    ('magician', 'Magik — moc, transformacja, spełnianie marzeń'),
                    ('hero', 'Bohater — mistrzostwo, odwaga, determinacja'),
                    ('lover', 'Kochanek — intymność, pasja, piękno'),
                    ('jester', 'Błazen — radość, humor, lekkość'),
                    ('everyman', 'Zwykły człowiek — przynależność, równość, realizm'),
                    ('caregiver', 'Opiekun — opiekuńczość, troska, bezpieczeństwo'),
                    ('ruler', 'Władca — kontrola, porządek, przywództwo'),
                    ('creator', 'Kreator — innowacyjność, wyobraźnia, tworzenie'),
                ],
            ),
        ),
    ]
