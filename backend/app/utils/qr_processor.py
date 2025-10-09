"""
Utilidades para procesamiento de códigos QR
Generación, lectura y validación de códigos QR
"""
import logging
import os
import uuid
import io
import json
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from pyzbar.pyzbar import decode
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

from ..config import get_settings
from ..schemas.qr_code import QRGenerationConfig, QRErrorCorrectionLevel

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class QRProcessorError(Exception):
    """Excepción personalizada para errores de procesamiento de QR"""
    pass


class QRProcessor:
    """
    Clase principal para procesamiento de códigos QR
    Maneja generación, lectura y validación
    """
    
    def __init__(self):
        """Inicializar el procesador de QR"""
        self.temp_path = settings.TEMP_PATH
        
        # Mapeo de niveles de corrección de errores
        self.error_correction_map = {
            QRErrorCorrectionLevel.L: ERROR_CORRECT_L,
            QRErrorCorrectionLevel.M: ERROR_CORRECT_M,
            QRErrorCorrectionLevel.Q: ERROR_CORRECT_Q,
            QRErrorCorrectionLevel.H: ERROR_CORRECT_H,
        }
        
        # Configuración por defecto
        self.default_config = QRGenerationConfig()
        
        logger.info("QRProcessor inicializado correctamente")
    
    # === GENERACIÓN DE QR ===
    
    def generate_qr_code(
        self,
        data: str,
        config: QRGenerationConfig = None,
        output_path: str = None,
        format: str = "PNG"
    ) -> str:
        """
        Generar código QR
        
        Args:
            data: Datos a codificar en el QR
            config: Configuración de generación
            output_path: Ruta de salida (se genera automáticamente si no se proporciona)
            format: Formato de imagen (PNG, JPEG, SVG)
            
        Returns:
            str: Ruta del archivo generado
            
        Raises:
            QRProcessorError: Si hay errores en la generación
        """
        try:
            if not config:
                config = self.default_config
            
            logger.info(f"Generando código QR para datos de {len(data)} caracteres")
            
            # Crear objeto QR
            error_correct = self.error_correction_map.get(
                config.error_correction, 
                ERROR_CORRECT_L
            )
            
            qr = qrcode.QRCode(
                version=config.version,
                error_correction=error_correct,
                box_size=config.box_size,
                border=config.border,
            )
            
            # Agregar datos
            qr.add_data(data)
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(
                fill_color=config.fill_color,
                back_color=config.back_color
            )
            
            # Generar ruta de salida si no se proporciona
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"qr_{timestamp}.{format.lower()}"
                output_path = os.path.join(self.temp_path, filename)
            
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Guardar imagen
            if format.upper() == "SVG":
                # Para SVG usar factory especial
                factory = qrcode.image.svg.SvgPathImage
                qr_svg = qrcode.QRCode(
                    version=config.version,
                    error_correction=error_correct,
                    box_size=config.box_size,
                    border=config.border,
                    image_factory=factory
                )
                qr_svg.add_data(data)
                qr_svg.make(fit=True)
                
                svg_img = qr_svg.make_image()
                svg_img.save(output_path)
            else:
                img.save(output_path, format=format.upper())
            
            logger.info(f"Código QR generado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generando código QR: {str(e)}")
            raise QRProcessorError(f"Error generando código QR: {str(e)}")
    
    def generate_qr_with_logo(
        self,
        data: str,
        logo_path: str,
        config: QRGenerationConfig = None,
        output_path: str = None,
        logo_size_ratio: float = 0.3
    ) -> str:
        """
        Generar código QR con logo en el centro
        
        Args:
            data: Datos a codificar
            logo_path: Ruta del logo
            config: Configuración de generación
            output_path: Ruta de salida
            logo_size_ratio: Ratio del tamaño del logo respecto al QR
            
        Returns:
            str: Ruta del archivo generado
        """
        try:
            if not config:
                config = self.default_config
            
            logger.info(f"Generando código QR con logo: {logo_path}")
            
            # Generar QR base
            qr_path = self.generate_qr_code(data, config, format="PNG")
            
            # Abrir imágenes
            qr_img = Image.open(qr_path)
            logo_img = Image.open(logo_path)
            
            # Calcular tamaño del logo
            qr_size = qr_img.size[0]
            logo_size = int(qr_size * logo_size_ratio)
            
            # Redimensionar logo manteniendo aspecto
            logo_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Crear fondo blanco para el logo
            logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
            
            # Calcular posición del logo en el fondo
            logo_pos = (
                (logo_bg.size[0] - logo_img.size[0]) // 2,
                (logo_bg.size[1] - logo_img.size[1]) // 2
            )
            
            # Pegar logo en fondo
            if logo_img.mode == 'RGBA':
                logo_bg.paste(logo_img, logo_pos, logo_img)
            else:
                logo_bg.paste(logo_img, logo_pos)
            
            # Calcular posición del logo en el QR
            qr_center = (
                (qr_size - logo_bg.size[0]) // 2,
                (qr_size - logo_bg.size[1]) // 2
            )
            
            # Pegar logo en QR
            qr_img.paste(logo_bg, qr_center)
            
            # Generar ruta de salida
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"qr_with_logo_{timestamp}.png"
                output_path = os.path.join(self.temp_path, filename)
            
            # Guardar imagen final
            qr_img.save(output_path, "PNG")
            
            # Limpiar archivo temporal
            try:
                os.remove(qr_path)
            except:
                pass
            
            logger.info(f"Código QR con logo generado: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generando QR con logo: {str(e)}")
            raise QRProcessorError(f"Error generando QR con logo: {str(e)}")
    
    def generate_batch_qr_codes(
        self,
        data_list: List[str],
        config: QRGenerationConfig = None,
        output_dir: str = None,
        name_prefix: str = "qr"
    ) -> List[str]:
        """
        Generar múltiples códigos QR en lote
        
        Args:
            data_list: Lista de datos para codificar
            config: Configuración de generación
            output_dir: Directorio de salida
            name_prefix: Prefijo para nombres de archivo
            
        Returns:
            List[str]: Lista de rutas de archivos generados
        """
        try:
            if not output_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(self.temp_path, f"qr_batch_{timestamp}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Generando {len(data_list)} códigos QR en lote")
            
            generated_files = []
            
            for i, data in enumerate(data_list, 1):
                try:
                    filename = f"{name_prefix}_{i:04d}.png"
                    output_path = os.path.join(output_dir, filename)
                    
                    qr_path = self.generate_qr_code(data, config, output_path)
                    generated_files.append(qr_path)
                    
                except Exception as e:
                    logger.warning(f"Error generando QR {i}: {str(e)}")
                    continue
            
            logger.info(f"Generados {len(generated_files)} códigos QR exitosamente")
            return generated_files
            
        except Exception as e:
            logger.error(f"Error en generación en lote: {str(e)}")
            raise QRProcessorError(f"Error generando códigos QR en lote: {str(e)}")
    
    # === LECTURA DE QR ===
    
    def read_qr_from_image(self, image_path: str) -> Optional[str]:
        """
        Leer código QR desde archivo de imagen
        
        Args:
            image_path: Ruta del archivo de imagen
            
        Returns:
            Optional[str]: Contenido del QR o None si no se encuentra
        """
        try:
            logger.info(f"Leyendo código QR desde imagen: {image_path}")
            
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                logger.warning(f"Archivo no encontrado: {image_path}")
                return None
            
            # Leer imagen con OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"No se pudo cargar la imagen: {image_path}")
                return None
            
            # Decodificar QR
            decoded_objects = decode(image)
            
            if not decoded_objects:
                # Intentar con preprocesamiento de imagen
                return self._read_qr_with_preprocessing(image)
            
            # Retornar contenido del primer QR encontrado
            qr_data = decoded_objects[0].data.decode('utf-8')
            logger.info(f"QR leído exitosamente: {qr_data[:50]}...")
            return qr_data
            
        except Exception as e:
            logger.error(f"Error leyendo QR desde imagen: {str(e)}")
            return None
    
    def read_qr_from_pdf(self, pdf_path: str, page_number: int = 0) -> Optional[str]:
        """
        Leer código QR desde archivo PDF
        
        Args:
            pdf_path: Ruta del archivo PDF
            page_number: Número de página (0-indexado)
            
        Returns:
            Optional[str]: Contenido del QR o None si no se encuentra
        """
        try:
            logger.info(f"Leyendo código QR desde PDF: {pdf_path}, página {page_number}")
            
            # Verificar que el archivo exists
            if not os.path.exists(pdf_path):
                logger.warning(f"Archivo PDF no encontrado: {pdf_path}")
                return None
            
            # Abrir PDF
            doc = fitz.open(pdf_path)
            
            if page_number >= len(doc):
                logger.warning(f"Página {page_number} no existe en el PDF")
                doc.close()
                return None
            
            # Obtener página
            page = doc[page_number]
            
            # Convertir a imagen con alta resolución
            zoom_matrix = fitz.Matrix(3, 3)  # Factor de zoom 3x para mejor detección
            pix = page.get_pixmap(matrix=zoom_matrix)
            
            # Convertir a array de numpy
            img_data = pix.samples
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            img_array = img_array.reshape(pix.height, pix.width, pix.n)
            
            # Convertir de RGB a BGR para OpenCV
            if pix.n == 3:  # RGB
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif pix.n == 4:  # RGBA
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else:
                img_bgr = img_array
            
            # Cerrar PDF
            doc.close()
            
            # Decodificar QR
            decoded_objects = decode(img_bgr)
            
            if not decoded_objects:
                # Intentar con preprocesamiento
                return self._read_qr_with_preprocessing(img_bgr)
            
            # Retornar contenido del primer QR
            qr_data = decoded_objects[0].data.decode('utf-8')
            logger.info(f"QR leído desde PDF exitosamente: {qr_data[:50]}...")
            return qr_data
            
        except Exception as e:
            logger.error(f"Error leyendo QR desde PDF: {str(e)}")
            return None
    
    def _read_qr_with_preprocessing(self, image: np.ndarray) -> Optional[str]:
        """
        Intentar leer QR con preprocesamiento de imagen
        
        Args:
            image: Imagen como array de numpy
            
        Returns:
            Optional[str]: Contenido del QR o None
        """
        try:
            logger.debug("Intentando lectura de QR con preprocesamiento")
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Lista de técnicas de preprocesamiento
            preprocessing_techniques = [
                # 1. Imagen original en gris
                lambda img: img,
                
                # 2. Binarización adaptativa
                lambda img: cv2.adaptiveThreshold(
                    img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                ),
                
                # 3. Binarización OTSU
                lambda img: cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                
                # 4. Ecualización de histograma
                lambda img: cv2.equalizeHist(img),
                
                # 5. Filtro gaussiano + binarización
                lambda img: cv2.threshold(
                    cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )[1],
                
                # 6. Morfología - apertura
                lambda img: cv2.morphologyEx(
                    cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
                    cv2.MORPH_OPEN,
                    cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                ),
                
                # 7. Inversión de colores
                lambda img: 255 - cv2.adaptiveThreshold(
                    img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
            ]
            
            # Probar cada técnica
            for i, technique in enumerate(preprocessing_techniques):
                try:
                    processed_img = technique(gray)
                    decoded_objects = decode(processed_img)
                    
                    if decoded_objects:
                        qr_data = decoded_objects[0].data.decode('utf-8')
                        logger.debug(f"QR leído con técnica {i + 1}: {qr_data[:50]}...")
                        return qr_data
                        
                except Exception as e:
                    logger.debug(f"Técnica {i + 1} falló: {str(e)}")
                    continue
            
            logger.debug("No se pudo leer QR con ninguna técnica de preprocesamiento")
            return None
            
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {str(e)}")
            return None
    
    def read_multiple_qr_codes(self, image_path: str) -> List[str]:
        """
        Leer múltiples códigos QR desde una imagen
        
        Args:
            image_path: Ruta del archivo de imagen
            
        Returns:
            List[str]: Lista de contenidos de QR encontrados
        """
        try:
            logger.info(f"Buscando múltiples códigos QR en: {image_path}")
            
            # Leer imagen
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            # Decodificar todos los QR
            decoded_objects = decode(image)
            
            qr_codes = []
            for obj in decoded_objects:
                try:
                    qr_data = obj.data.decode('utf-8')
                    qr_codes.append(qr_data)
                except:
                    continue
            
            logger.info(f"Encontrados {len(qr_codes)} códigos QR")
            return qr_codes
            
        except Exception as e:
            logger.error(f"Error leyendo múltiples QR: {str(e)}")
            return []
    
    # === VALIDACIÓN Y ANÁLISIS ===
    
    def validate_qr_content(self, content: str, expected_format: str = None) -> Tuple[bool, str]:
        """
        Validar contenido de código QR
        
        Args:
            content: Contenido del QR
            expected_format: Formato esperado (uuid, json, url, etc.)
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        try:
            if not content:
                return False, "Contenido vacío"
            
            if expected_format == "uuid":
                # Validar formato UUID
                try:
                    uuid.UUID(content)
                    return True, "UUID válido"
                except ValueError:
                    return False, "No es un UUID válido"
            
            elif expected_format == "json":
                # Validar formato JSON
                try:
                    json.loads(content)
                    return True, "JSON válido"
                except json.JSONDecodeError as e:
                    return False, f"JSON inválido: {str(e)}"
            
            elif expected_format == "url":
                # Validar formato URL
                if content.startswith(('http://', 'https://')):
                    return True, "URL válida"
                else:
                    return False, "No es una URL válida"
            
            else:
                # Validación genérica
                if len(content) > 2000:
                    return False, "Contenido demasiado largo"
                
                # Verificar caracteres válidos
                try:
                    content.encode('utf-8')
                    return True, "Contenido válido"
                except UnicodeEncodeError:
                    return False, "Caracteres inválidos"
            
        except Exception as e:
            return False, f"Error validando contenido: {str(e)}"
    
    def analyze_qr_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analizar imagen de código QR y extraer información
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            dict: Información del análisis
        """
        try:
            logger.info(f"Analizando imagen QR: {image_path}")
            
            # Información básica del archivo
            file_stats = os.stat(image_path)
            file_info = {
                "file_size": file_stats.st_size,
                "file_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "file_path": image_path
            }
            
            # Información de la imagen
            with Image.open(image_path) as img:
                image_info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
            
            # Leer QR
            qr_content = self.read_qr_from_image(image_path)
            
            # Información del QR
            qr_info = {
                "has_qr": bool(qr_content),
                "content": qr_content,
                "content_length": len(qr_content) if qr_content else 0
            }
            
            if qr_content:
                # Detectar tipo de contenido
                content_type = "text"
                if qr_content.startswith(('http://', 'https://')):
                    content_type = "url"
                elif qr_content.startswith(('{', '[')):
                    content_type = "json"
                else:
                    try:
                        uuid.UUID(qr_content)
                        content_type = "uuid"
                    except:
                        pass
                
                qr_info["content_type"] = content_type
                
                # Validar contenido
                is_valid, validation_msg = self.validate_qr_content(qr_content, content_type)
                qr_info["is_valid"] = is_valid
                qr_info["validation_message"] = validation_msg
            
            return {
                "file_info": file_info,
                "image_info": image_info,
                "qr_info": qr_info,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analizando imagen QR: {str(e)}")
            return {
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    # === UTILIDADES ===
    
    def create_qr_data_structure(
        self,
        qr_id: str,
        document_type_code: str,
        additional_data: Dict[str, Any] = None
    ) -> str:
        """
        Crear estructura de datos estándar para QR
        
        Args:
            qr_id: ID único del QR
            document_type_code: Código del tipo de documento
            additional_data: Datos adicionales
            
        Returns:
            str: Datos estructurados como JSON string
        """
        try:
            data_structure = {
                "qr_id": qr_id,
                "document_type": document_type_code,
                "version": "1.0",
                "generated_at": datetime.utcnow().isoformat(),
                "system": "SGD_Web"
            }
            
            if additional_data:
                data_structure.update(additional_data)
            
            return json.dumps(data_structure, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error creando estructura de datos: {str(e)}")
            # Fallback a ID simple si falla JSON
            return qr_id
    
    def parse_qr_data_structure(self, qr_content: str) -> Dict[str, Any]:
        """
        Parsear estructura de datos de QR
        
        Args:
            qr_content: Contenido del QR
            
        Returns:
            dict: Datos parseados
        """
        try:
            # Intentar parsear como JSON
            try:
                data = json.loads(qr_content)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
            
            # Si no es JSON, asumir que es un ID simple
            return {
                "qr_id": qr_content,
                "version": "simple",
                "system": "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error parseando datos de QR: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Limpiar archivos temporales antiguos
        
        Args:
            max_age_hours: Edad máxima en horas
        """
        try:
            logger.info(f"Limpiando archivos temporales mayores a {max_age_hours} horas")
            
            current_time = datetime.now()
            deleted_count = 0
            
            for file_path in Path(self.temp_path).glob("qr_*"):
                try:
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_age.total_seconds() > (max_age_hours * 3600):
                        file_path.unlink()
                        deleted_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error eliminando archivo {file_path}: {str(e)}")
            
            logger.info(f"Eliminados {deleted_count} archivos temporales")
            
        except Exception as e:
            logger.error(f"Error limpiando archivos temporales: {str(e)}")


# === INSTANCIA GLOBAL ===

# Instancia singleton del procesador
_qr_processor = None

def get_qr_processor() -> QRProcessor:
    """
    Obtener instancia del procesador de QR
    
    Returns:
        QRProcessor: Instancia del procesador
    """
    global _qr_processor
    if _qr_processor is None:
        _qr_processor = QRProcessor()
    return _qr_processor


# === FUNCIONES DE UTILIDAD ===

def generate_unique_qr_id() -> str:
    """
    Generar ID único para código QR
    
    Returns:
        str: UUID único
    """
    return str(uuid.uuid4())


def is_valid_qr_format(content: str) -> bool:
    """
    Verificar si el contenido tiene formato válido para QR
    
    Args:
        content: Contenido a verificar
        
    Returns:
        bool: True si es válido
    """
    try:
        processor = get_qr_processor()
        is_valid, _ = processor.validate_qr_content(content)
        return is_valid
    except:
        return False


def extract_qr_from_file(file_path: str) -> Optional[str]:
    """
    Extraer contenido de QR desde archivo (imagen o PDF)

    Args:
        file_path: Ruta del archivo

    Returns:
        Optional[str]: Contenido del QR o None
    """
    try:
        processor = get_qr_processor()

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.pdf':
            return processor.read_qr_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return processor.read_qr_from_image(file_path)
        else:
            logger.warning(f"Tipo de archivo no soportado para extracción de QR: {file_ext}")
            return None

    except Exception as e:
        logger.error(f"Error extrayendo QR de archivo: {str(e)}")
        return None


def extract_qr_with_status(file_path: str) -> Dict[str, Any]:
    """
    Extraer contenido de QR desde archivo con información de estado detallada.
    Implementa el patrón QR OPCIONAL: intenta extraer QR pero NO falla si no existe.

    Args:
        file_path: Ruta del archivo

    Returns:
        Dict con:
            - tiene_qr (bool): Si se detectó un QR en el documento
            - qr_code (str|None): Contenido del QR si se encontró
            - qr_extraction_success (bool): Si la extracción fue exitosa
            - qr_extraction_error (str|None): Mensaje de error si aplica
            - qr_extraction_data (dict|None): Datos parseados del QR
    """
    result = {
        "tiene_qr": False,
        "qr_code": None,
        "qr_extraction_success": False,
        "qr_extraction_error": None,
        "qr_extraction_data": None
    }

    try:
        processor = get_qr_processor()

        file_ext = os.path.splitext(file_path)[1].lower()

        # Verificar que el tipo de archivo sea soportado
        if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            result["qr_extraction_error"] = f"Tipo de archivo no soportado para extracción de QR: {file_ext}"
            logger.info(f"Tipo de archivo no soportado para QR: {file_ext}. Continuando sin QR.")
            return result

        # Intentar extraer QR según el tipo de archivo
        qr_content = None
        if file_ext == '.pdf':
            qr_content = processor.read_qr_from_pdf(file_path)
        else:
            qr_content = processor.read_qr_from_image(file_path)

        # Si se encontró contenido QR
        if qr_content:
            result["tiene_qr"] = True
            result["qr_code"] = qr_content
            result["qr_extraction_success"] = True

            # Intentar parsear datos estructurados
            try:
                parsed_data = processor.parse_qr_data_structure(qr_content)
                result["qr_extraction_data"] = parsed_data
            except Exception as parse_error:
                logger.warning(f"No se pudo parsear datos del QR: {str(parse_error)}")
                # No es un error crítico, el QR se extrajo correctamente

            logger.info(f"QR extraído exitosamente del archivo: {file_path}")
        else:
            # No se encontró QR - esto NO es un error
            result["tiene_qr"] = False
            result["qr_extraction_success"] = False
            result["qr_extraction_error"] = "No se detectó código QR en el documento"
            logger.info(f"No se detectó QR en el archivo: {file_path}. Continuando sin QR.")

        return result

    except Exception as e:
        # Error en el proceso de extracción
        error_message = f"Error durante extracción de QR: {str(e)}"
        result["tiene_qr"] = False
        result["qr_extraction_success"] = False
        result["qr_extraction_error"] = error_message
        logger.warning(f"{error_message}. Continuando sin QR.")
        return result