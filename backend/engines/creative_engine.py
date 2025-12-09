"""
Creative Engine

Generates creative briefs and copy.

Input: Selected scenarios, segments, brand rules
Output: CreativeBrief with:
- Objectives and messaging
- Asset list
- Copy examples
- Layout hints
"""

from typing import List, Optional, Dict, Any

from models.schemas import PromoScenario, CreativeBrief, AssetSpec
from tools.cdp_tool import CDPTool
from tools.targets_config_tool import TargetsConfigTool


class CreativeEngine:
    """Engine for generating creative briefs and asset copy."""
    
    def __init__(
        self,
        cdp_tool: Optional[CDPTool] = None,
        config_tool: Optional[TargetsConfigTool] = None,
    ):
        """
        Initialize Creative Engine.
        
        Args:
            cdp_tool: CDP Tool instance for segment data
            config_tool: Targets & Config Tool instance for brand rules
        """
        self.cdp_tool = cdp_tool
        self.config_tool = config_tool
    
    def generate_creative_brief(
        self,
        scenario: PromoScenario,
        segments: Optional[List[str]] = None,
        brand_rules: Optional[Dict[str, Any]] = None
    ) -> CreativeBrief:
        """
        Generate structured creative brief from scenario.
        
        Args:
            scenario: PromoScenario to generate brief for
            segments: Optional list of target segments
            brand_rules: Optional brand rules dictionary
        
        Returns:
            CreativeBrief with objectives, messaging, tone, style
        """
        from models.schemas import CreativeBrief
        
        # Get brand rules from config tool if not provided
        if brand_rules is None and self.config_tool:
            brand_rules_obj = self.config_tool.get_brand_rules()
            brand_rules = {
                "tone_guidelines": brand_rules_obj.tone_guidelines,
                "style_requirements": brand_rules_obj.style_requirements,
                "mandatory_elements": brand_rules_obj.mandatory_elements,
            }
        
        # Build objectives
        objectives = [
            f"Drive sales in {', '.join(scenario.departments)} departments",
            f"Reach customers across {', '.join(scenario.channels)} channels",
            f"Offer {scenario.discount_percentage}% discount to maximize impact",
        ]
        
        if segments:
            objectives.append(f"Target segments: {', '.join(segments)}")
        
        # Build messaging
        discount_str = f"{scenario.discount_percentage:.0f}%"
        dept_str = ", ".join(scenario.departments)
        messaging = (
            f"Promote {discount_str} discount on {dept_str} products "
            f"across {', '.join(scenario.channels)} channels. "
            f"Campaign runs from {scenario.date_range.start_date} to {scenario.date_range.end_date}. "
            f"Focus on value proposition and clear call-to-action."
        )
        
        # Determine tone and style from brand rules
        tone = "confident"  # Default
        style = "benefit-led"  # Default
        
        if brand_rules:
            tone_guidelines = brand_rules.get("tone_guidelines", [])
            if tone_guidelines:
                tone = tone_guidelines[0] if isinstance(tone_guidelines[0], str) else "confident"
            
            style_requirements = brand_rules.get("style_requirements", [])
            if style_requirements:
                style = style_requirements[0] if isinstance(style_requirements[0], str) else "benefit-led"
        
        # Mandatory elements
        mandatory_elements = [
            f"Discount: {scenario.discount_percentage}%",
            f"Departments: {', '.join(scenario.departments)}",
            f"Date range: {scenario.date_range.start_date} to {scenario.date_range.end_date}",
            f"Channels: {', '.join(scenario.channels)}",
        ]
        
        if brand_rules and brand_rules.get("mandatory_elements"):
            mandatory_elements.extend(brand_rules["mandatory_elements"])
        
        # Target audience
        target_audience = "General consumers"
        if segments:
            target_audience = f"Target segments: {', '.join(segments)}"
        
        return CreativeBrief(
            scenario_id=scenario.id or "unknown",
            objectives=objectives,
            messaging=messaging,
            target_audience=target_audience,
            tone=tone,
            style=style,
            mandatory_elements=mandatory_elements
        )
    
    def generate_asset_specs(
        self,
        brief: CreativeBrief
    ) -> List[AssetSpec]:
        """
        Generate asset specifications from creative brief.
        
        Args:
            brief: CreativeBrief to generate assets from
        
        Returns:
            List of AssetSpec objects (homepage hero, banners, in-store, etc.)
        """
        from models.schemas import AssetSpec
        
        assets = []
        
        # Homepage hero
        hero_copy = self.generate_copy("homepage_hero", brief)
        assets.append(AssetSpec(
            asset_type="homepage_hero",
            copy_text=hero_copy,
            dimensions={"width": 1920, "height": 600},
            layout_hints={"headline": "large", "cta": "prominent"}
        ))
        
        # Banner
        banner_copy = self.generate_copy("banner", brief)
        assets.append(AssetSpec(
            asset_type="banner",
            copy_text=banner_copy,
            dimensions={"width": 728, "height": 90},
            layout_hints={"headline": "medium", "cta": "visible"}
        ))
        
        # In-store
        instore_copy = self.generate_copy("instore", brief)
        assets.append(AssetSpec(
            asset_type="instore",
            copy_text=instore_copy,
            dimensions={"width": 600, "height": 800},
            layout_hints={"headline": "large", "details": "clear"}
        ))
        
        # Email header
        email_copy = self.generate_copy("email_header", brief)
        assets.append(AssetSpec(
            asset_type="email_header",
            copy_text=email_copy,
            dimensions={"width": 600, "height": 200},
            layout_hints={"headline": "medium", "cta": "button"}
        ))
        
        return assets
    
    def generate_copy(
        self,
        asset_type: str,
        brief: CreativeBrief,
        segment: Optional[str] = None
    ) -> str:
        """
        Generate copy for specific asset type.
        
        Args:
            asset_type: Type of asset (homepage_hero, banner, instore, etc.)
            brief: CreativeBrief with context
            segment: Optional target segment
        
        Returns:
            Copy string for the asset
        """
        # Extract discount from mandatory elements
        discount = "15%"
        for elem in brief.mandatory_elements:
            if "Discount:" in elem:
                discount = elem.split("Discount:")[1].strip()
                break
        
        # Base messaging
        base_message = brief.messaging
        
        # Asset-specific copy
        if asset_type == "homepage_hero":
            copy = f"{brief.tone.title()} headline: Save {discount} on {brief.messaging.split('on ')[1].split(' products')[0] if 'on ' in brief.messaging else 'selected products'}. {brief.messaging.split('.')[1] if '.' in brief.messaging else 'Limited time offer.'}"
        elif asset_type == "banner":
            copy = f"{discount} OFF - {brief.messaging.split('.')[0]}"
        elif asset_type == "instore":
            copy = f"IN-STORE: {brief.messaging}. Visit our stores for exclusive deals."
        elif asset_type == "email_header":
            copy = f"Special Offer: {discount} Discount. {brief.messaging.split('.')[0]}"
        else:
            copy = brief.messaging
        
        # Add segment-specific messaging if provided
        if segment:
            copy = f"For {segment}: {copy}"
        
        return copy

