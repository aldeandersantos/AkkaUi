from .models import SvgFile




def del_svg_file(svg_file_id):
    try:
        svg_file = SvgFile.objects.get(id=svg_file_id)
        svg_file.delete()
        return True
    except SvgFile.DoesNotExist:
        return False