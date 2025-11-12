import pytest
from core.services import del_svg_file
from core.models import SvgFile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.services
@pytest.mark.django_db
class TestDelSvgFileService:
    def test_delete_existing_svg(self, svg_file):
        svg_id = svg_file.id
        result = del_svg_file(svg_id)
        
        assert result is True
        assert not SvgFile.objects.filter(id=svg_id).exists()
    
    def test_delete_non_existing_svg(self):
        result = del_svg_file(99999)
        assert result is False
    
    def test_delete_svg_removes_from_database(self, user):
        svg = SvgFile.objects.create(
            title_name='To Delete',
            content='<svg></svg>',
            owner=user
        )
        svg_id = svg.id
        
        initial_count = SvgFile.objects.count()
        del_svg_file(svg_id)
        
        assert SvgFile.objects.count() == initial_count - 1
