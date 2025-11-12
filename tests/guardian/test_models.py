import pytest
from django.core.exceptions import ValidationError
from guardian.models import FileAsset, validate_file_path
from django.contrib.auth import get_user_model
from pathlib import Path

User = get_user_model()


@pytest.mark.utils
@pytest.mark.django_db
class TestValidateFilePath:
    def test_validate_relative_path(self):
        result = validate_file_path('uploads/file.pdf')
        assert result == 'uploads/file.pdf'
    
    def test_validate_empty_path_raises_error(self):
        with pytest.raises(ValidationError) as exc:
            validate_file_path('')
        assert 'não pode estar vazio' in str(exc.value)
    
    def test_validate_absolute_path_raises_error(self):
        with pytest.raises(ValidationError) as exc:
            validate_file_path('/etc/passwd')
        msg = str(exc.value)
        # Aceita mensagens diferentes dependendo da plataforma/implementação:
        # - 'relativo' quando a função detecta caminho absoluto explicitamente
        # - menção a 'fora do MEDIA_ROOT' ou 'directory traversal' quando a
        #   validação via resolve() considera o caminho fora do MEDIA_ROOT
        assert (
            'relativo' in msg
            or 'fora do MEDIA_ROOT' in msg
            or 'directory traversal' in msg
            or 'resolve para fora' in msg
        )
    
    def test_validate_directory_traversal_raises_error(self):
        with pytest.raises(ValidationError) as exc:
            validate_file_path('../../../etc/passwd')
        assert 'directory traversal' in str(exc.value)
    
    def test_validate_normalizes_path(self):
        result = validate_file_path('uploads//file.pdf')
        assert result == 'uploads/file.pdf'


@pytest.mark.models
@pytest.mark.django_db
class TestFileAssetModel:
    def test_create_file_asset(self, user):
        asset = FileAsset.objects.create(
            name='Test File',
            file_path='uploads/test.pdf',
            owner=user
        )
        assert asset.name == 'Test File'
        assert asset.file_path == 'uploads/test.pdf'
        assert asset.owner == user
    
    def test_file_asset_str_representation(self, user):
        asset = FileAsset.objects.create(
            name='Document',
            file_path='docs/file.pdf',
            owner=user
        )
        str_repr = str(asset)
        assert 'Document' in str_repr
        assert 'docs/file.pdf' in str_repr
    
    def test_file_asset_uploaded_at_timestamp(self, user):
        asset = FileAsset.objects.create(
            name='Test',
            file_path='test.pdf',
            owner=user
        )
        assert asset.uploaded_at is not None
    
    def test_file_asset_invalid_path_raises_error(self, user):
        with pytest.raises(ValidationError):
            asset = FileAsset(
                name='Invalid',
                file_path='../../../etc/passwd',
                owner=user
            )
            asset.full_clean()
    
    def test_file_asset_clean_validates_path(self, user):
        asset = FileAsset(
            name='Test',
            file_path='uploads//file.pdf',
            owner=user
        )
        asset.clean()
        assert asset.file_path == 'uploads/file.pdf'
