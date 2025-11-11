from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
import io


class ReceiptGenerator:
    """Generate PDF receipts for payments"""
    
    def generate_receipt(self, receipt_data):
        """
        Generate PDF receipt
        
        Args:
            receipt_data: Dictionary with receipt information
        
        Returns:
            BytesIO buffer containing PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        
        # Title
        elements.append(Paragraph("PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Receipt details
        elements.append(Paragraph(f"Receipt Number: {receipt_data['receipt_number']}", styles['Normal']))
        elements.append(Paragraph(f"Date: {receipt_data['payment_date']}", styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Parent details
        elements.append(Paragraph("PAID BY", heading_style))
        parent_data = [
            ['Name:', receipt_data['parent']['name']],
            ['Email:', receipt_data['parent']['email']],
            ['Phone:', receipt_data['parent']['phone']]
        ]
        parent_table = Table(parent_data, colWidths=[1.5 * inch, 4 * inch])
        parent_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(parent_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Payment details
        elements.append(Paragraph("PAYMENT DETAILS", heading_style))
        payment_data = [
            ['Reference Number:', receipt_data['payment']['reference_number']],
            ['Amount:', f"{receipt_data['payment']['currency']} {receipt_data['payment']['amount']:,.2f}"],
            ['Payment Method:', receipt_data['payment']['payment_method'].upper()],
            ['M-Pesa Receipt:', receipt_data['payment']['mpesa_receipt'] or 'N/A']
        ]
        payment_table = Table(payment_data, colWidths=[1.5 * inch, 4 * inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Registration details
        elements.append(Paragraph("TRIP DETAILS", heading_style))
        trip_data = [
            ['Trip:', receipt_data['registration']['trip_title']],
            ['Participant:', receipt_data['registration']['participant_name']],
            ['Trip Dates:', receipt_data['registration']['trip_dates']],
            ['Registration #:', receipt_data['registration']['registration_number']]
        ]
        trip_table = Table(trip_data, colWidths=[1.5 * inch, 4 * inch])
        trip_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        elements.append(trip_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Balance summary
        elements.append(Paragraph("BALANCE SUMMARY", heading_style))
        balance_data = [
            ['Total Amount:', f"{receipt_data['payment']['currency']} {receipt_data['balance']['total_amount']:,.2f}"],
            ['Amount Paid:', f"{receipt_data['payment']['currency']} {receipt_data['balance']['amount_paid']:,.2f}"],
            ['Outstanding Balance:', f"{receipt_data['payment']['currency']} {receipt_data['balance']['outstanding_balance']:,.2f}"]
        ]
        balance_table = Table(balance_data, colWidths=[1.5 * inch, 4 * inch])
        balance_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold')
        ]))
        elements.append(balance_table)
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Thank you for your payment!", footer_style))
        elements.append(Paragraph("For inquiries, contact support@edusafaris.com", footer_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

