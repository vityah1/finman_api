import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy import or_
from models.models import UtilityTariff, UtilityReading, UtilityService
from mydb import db

logger = logging.getLogger()


class UtilityCalculationService:
    """Сервіс для розширених розрахунків комунальних платежів"""
    
    @staticmethod
    def get_grouped_tariffs(service_id: int, period: str) -> Dict[str, List[UtilityTariff]]:
        """Отримати згруповані тарифи для служби на заданий період"""
        # Парсимо період для визначення дати
        period_date = datetime.strptime(f"{period}-01", "%Y-%m-%d")
        
        # Знаходимо всі активні тарифи для служби на цей період
        tariffs = db.session().query(UtilityTariff).filter(
            UtilityTariff.service_id == service_id,
            UtilityTariff.is_active == True,
            UtilityTariff.valid_from <= period_date,
            or_(
                UtilityTariff.valid_to.is_(None),
                UtilityTariff.valid_to >= period_date
            )
        ).all()
        
        # Групуємо тарифи за group_code
        grouped = {}
        for tariff in tariffs:
            group = tariff.group_code or 'default'
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(tariff)
        
        return grouped
    
    @staticmethod
    def calculate_shared_meter_charges(consumption: float, tariffs: List[UtilityTariff]) -> Dict:
        """Розрахунок для спільного показника з групою тарифів"""
        details = {
            'components': [],
            'total_amount': 0,
            'subscription_fee': 0
        }
        
        # Знаходимо основний тариф (без percentage_of або з calculation_method='standard')
        main_tariff = next((t for t in tariffs if t.calculation_method == 'standard' and t.tariff_type != 'subscription'), None)
        if not main_tariff:
            # Якщо немає явно вказаного стандартного тарифу, шукаємо будь-який не subscription
            main_tariff = next((t for t in tariffs if t.tariff_type != 'subscription'), None)
        
        if not main_tariff and tariffs:
            # Якщо всі тарифи subscription, беремо перший
            main_tariff = tariffs[0]
        
        # Спочатку обробляємо основний тариф
        if main_tariff:
            # Перевіряємо тип тарифу
            if main_tariff.tariff_type == 'subscription':
                # Абонплата - фіксована сума, не залежить від споживання
                consumption_amount = main_tariff.rate
                details['components'].append({
                    'name': main_tariff.name,
                    'type': 'subscription',
                    'consumption': 0,  # Для абонплати споживання не враховується
                    'rate': main_tariff.rate,
                    'amount': consumption_amount
                })
            else:
                # Стандартний розрахунок за споживанням
                consumption_amount = consumption * main_tariff.rate
                details['components'].append({
                    'name': main_tariff.name,
                    'type': main_tariff.tariff_type or 'standard',
                    'consumption': consumption,
                    'rate': main_tariff.rate,
                    'amount': consumption_amount
                })
            
            details['total_amount'] += consumption_amount
            
            # Додаємо абонплату основного тарифу як окремий компонент, але не додаємо до total_amount
            # (абонплата буде збережена окремим записом)
            if main_tariff.subscription_fee:
                details['subscription_fee'] = main_tariff.subscription_fee
                # Додаємо компонент абонплати, але не додаємо до загальної суми
                details['components'].append({
                    'name': main_tariff.name,
                    'type': 'subscription',
                    'consumption': 0,
                    'rate': main_tariff.subscription_fee,
                    'amount': main_tariff.subscription_fee
                })
        
        # Розрахунок додаткових тарифів (percentage або fixed)
        for tariff in tariffs:
            # Пропускаємо основний тариф, оскільки ми його вже обробили
            if tariff.id == main_tariff.id:
                continue
            
            # Пропускаємо тарифи типу 'subscription' - вони будуть додані окремими записами
            if tariff.tariff_type == 'subscription':
                # Додаємо в компоненти для інформації, але не включаємо в total_amount
                details['components'].append({
                    'name': tariff.name,
                    'type': 'subscription',
                    'consumption': 0,
                    'rate': tariff.rate,
                    'amount': tariff.rate
                })
                continue
                
            # Розрахунок для інших типів тарифів
            if tariff.calculation_method == 'percentage' and tariff.percentage_of:
                # Розраховуємо як відсоток від основного
                additional_amount = consumption_amount * (tariff.percentage_of / 100)
                consumption_for_display = consumption
            elif tariff.calculation_method == 'fixed':
                # Фіксована сума
                additional_amount = tariff.rate
                consumption_for_display = 0
            else:
                # Стандартний розрахунок за тарифом
                additional_amount = consumption * tariff.rate
                consumption_for_display = consumption
            
            details['components'].append({
                'name': tariff.name,
                'type': tariff.tariff_type or 'additional',
                'consumption': consumption_for_display,
                'rate': tariff.rate,
                'percentage_of': tariff.percentage_of,
                'calculation_method': tariff.calculation_method,
                'amount': additional_amount
            })
            details['total_amount'] += additional_amount
        
        return details
    
    @staticmethod
    def calculate_multiple_meter_charges(readings: List[Dict], tariffs: List[UtilityTariff]) -> Dict:
        """Розрахунок для множинних показників (різні лічильники)"""
        details = {
            'components': [],
            'total_amount': 0,
            'subscription_fee': 0
        }
        
        # Обробляємо кожен тип показника
        for reading in readings:
            reading_type = reading.get('reading_type', 'standard')
            consumption = reading.get('consumption', 0)
            
            # Знаходимо відповідний тариф
            tariff = next((t for t in tariffs if t.tariff_type == reading_type), None)
            if not tariff and tariffs:
                tariff = tariffs[0]  # Fallback до першого тарифу
            
            if tariff:
                amount = consumption * tariff.rate
                details['components'].append({
                    'name': tariff.name,
                    'type': reading_type,
                    'consumption': consumption,
                    'rate': tariff.rate,
                    'amount': amount
                })
                details['total_amount'] += amount
                
                # Абонплата додається лише один раз
                if tariff.subscription_fee and details['subscription_fee'] == 0:
                    details['subscription_fee'] = tariff.subscription_fee
                    details['total_amount'] += tariff.subscription_fee
        
        return details
    
    @staticmethod
    def calculate_reading_amount(service: UtilityService, reading_data: Dict, grouped_tariffs: Dict) -> Dict:
        """Універсальний метод розрахунку суми для показників"""
        
        # Якщо служба має спільний показник (has_shared_meter=True)
        if service.has_shared_meter:
            # Використовуємо групу тарифів
            group_code = reading_data.get('tariff_group', 'default')
            tariffs = grouped_tariffs.get(group_code, [])
            
            consumption = reading_data['current_reading'] - reading_data.get('previous_reading', 0)
            
            # Розрахунок для спільного показника з групою тарифів
            result = UtilityCalculationService.calculate_shared_meter_charges(consumption, tariffs)
            
            # Логуємо для перевірки
            logger.info(f"Shared meter calculation for service {service.name}, group {group_code}:")
            logger.info(f"Tariffs: {[t.name for t in tariffs]}")
            logger.info(f"Result: {result}")
            
            return result
            
        elif 'readings' in reading_data:
            # Множинні показники (різні лічильники)
            tariffs = []
            for group in grouped_tariffs.values():
                tariffs.extend(group)
            return UtilityCalculationService.calculate_multiple_meter_charges(
                reading_data['readings'], tariffs
            )
        else:
            # Стандартний розрахунок для одного показника
            consumption = reading_data['current_reading'] - reading_data.get('previous_reading', 0)
            tariff_id = reading_data.get('tariff_id')
            tariff = db.session().query(UtilityTariff).get(tariff_id)
            
            if tariff:
                # Перевіряємо, чи тариф є абонплатою
                if tariff.tariff_type == 'subscription':
                    return {
                        'components': [{
                            'name': tariff.name,
                            'type': 'subscription',
                            'consumption': 0,
                            'rate': tariff.rate,
                            'amount': tariff.rate
                        }],
                        'total_amount': tariff.rate,
                        'subscription_fee': 0
                    }
                else:
                    amount = consumption * tariff.rate
                    subscription = tariff.subscription_fee or 0
                    
                    result = {
                        'components': [{
                            'name': tariff.name,
                            'type': tariff.tariff_type or 'standard',
                            'consumption': consumption,
                            'rate': tariff.rate,
                            'amount': amount
                        }],
                        'total_amount': amount,
                        'subscription_fee': subscription
                    }
                    
                    # Якщо є абонплата, додаємо її як окремий компонент, але не в total_amount
                    if subscription > 0:
                        result['components'].append({
                            'name': f"{tariff.name} (абонплата)",
                            'type': 'subscription',
                            'consumption': 0,
                            'rate': subscription,
                            'amount': subscription
                        })
                    
                    return result
        
        return {
            'components': [],
            'total_amount': 0,
            'subscription_fee': 0
        }
