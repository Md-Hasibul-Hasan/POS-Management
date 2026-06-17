# =============================================================================
#  CATALOG: Category, Brand, Unit, Tag, Attributes, Media, Reviews
# =============================================================================

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import hashlib
import json

from .common import BaseModel

User = get_user_model()


# =============================================================================
#  CATEGORY, BRAND, UNIT, TAG
# =============================================================================

class Category(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'parent'], name='unique_category_name_per_parent')
        ]

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.parent and self.parent.pk == self.pk:
            raise ValidationError('A category cannot be its own parent.')
        if self.parent and self._is_circular_parent(self.parent):
            raise ValidationError('Circular category reference detected.')

    def _is_circular_parent(self, parent):
        visited = {self.pk}
        current = parent
        while current:
            if current.pk in visited:
                return True
            visited.add(current.pk)
            current = current.parent
        return False

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.clean()
        super().save(*args, **kwargs)


class Brand(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, default='')
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)
    banner = models.ImageField(upload_to='brands/banners/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Unit(BaseModel):
    UNIT_TYPE_CHOICES = [('weight', 'Weight'), ('volume', 'Volume'), ('length', 'Length'), ('piece', 'Piece'), ('other', 'Other')]
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, blank=True, default='')
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='piece')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =============================================================================
#  PRODUCT ATTRIBUTES
# =============================================================================

class Attribute(BaseModel):
    ATTRIBUTE_TYPE_CHOICES = [('text', 'Text'), ('color', 'Color'), ('image', 'Image'), ('number', 'Number')]
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    attribute_type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPE_CHOICES, default='text')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class AttributeValue(BaseModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=255)
    color_code = models.CharField(max_length=20, null=True, blank=True)
    image = models.ImageField(upload_to='attributes/values/', null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['attribute', 'value'], name='unique_attribute_value')]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class VariantAttribute(models.Model):
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField(max_length=255)
    attribute_value = models.CharField(max_length=255)

    class Meta:
        ordering = ['attribute_name']

    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value}"


def generate_attribute_signature(variant):
    attrs = variant.attributes.all().order_by('attribute_name', 'attribute_value')
    data = json.dumps([(a.attribute_name, a.attribute_value) for a in attrs], sort_keys=True)
    return hashlib.md5(data.encode()).hexdigest()


# =============================================================================
#  PRODUCT MEDIA
# =============================================================================

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True, default='')
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Image for {self.product.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_primary:
            existing = ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError('Only one primary image is allowed per product.')
        if self.variant and self.variant.product != self.product:
            raise ValidationError('Image variant must belong to the same product.')


class ProductVideo(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='videos')
    url = models.URLField()
    title = models.CharField(max_length=255, blank=True, default='')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Video for {self.product.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        url = self.url.lower()
        if 'youtube.com' in url or 'youtu.be' in url or 'vimeo.com' in url:
            return
        raise ValidationError('Video URL must be from YouTube or Vimeo.')


class ReviewImage(models.Model):
    review = models.ForeignKey('ProductReview', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    alt_text = models.CharField(max_length=255, blank=True, default='')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Image for review by {self.review.user.email}"


# =============================================================================
#  PRODUCT REVIEWS & FAQ
# =============================================================================

class ProductFAQ(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"FAQ: {self.question[:50]}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.question.strip():
            raise ValidationError({'question': 'Question cannot be empty.'})
        if not self.answer.strip():
            raise ValidationError({'answer': 'Answer cannot be empty.'})


class ProductReview(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey('OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255, blank=True, default='')
    comment = models.TextField(blank=True, default='')

    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    moderation_status = models.CharField(max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    is_verified_purchase = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['order_item'], name='unique_review_per_order_item')]

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}/5)"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_verified_purchase and self.order_item:
            if self.order_item.order.user != self.user:
                raise ValidationError('Review user must own the order item.')
            if self.order_item.product != self.product:
                raise ValidationError('Review product must match the order item product.')
            if self.order_item.order.status != 'delivered':
                raise ValidationError('Only delivered orders can be reviewed.')