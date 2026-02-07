"""
LinkedIn Post Generator Module for the Personal AI Employee system.
Generates engaging LinkedIn posts based on business achievements and milestones.
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional


def generate_linkedin_post(business_data: Dict) -> str:
    """
    Generate a LinkedIn post based on business achievement data.

    Args:
        business_data: Dictionary containing business achievement information

    Returns:
        Generated LinkedIn post content
    """

    # Determine the type of achievement and generate appropriate content
    achievement_type = business_data.get('type', 'general')

    # Define templates for different types of achievements
    templates = {
        'revenue': [
            "🎉 Great news! We've reached a significant milestone in our revenue journey. "
            "Our team's dedication and innovative approach continue to drive exceptional results. "
            "Grateful for our amazing customers who make this possible! #BusinessGrowth #Success",

            "🚀 Exciting times ahead! We've achieved a major revenue milestone that reflects "
            "our commitment to excellence and customer value. This achievement is a testament "
            "to our talented team and strong market demand. Here's to continued growth! #RevenueMilestone #TeamWork",

            "💪 Proud to share that we've hit an impressive revenue target! This achievement "
            "validates our strategic vision and the trust our clients place in us. "
            "Thank you to our incredible team for making this possible. #BusinessSuccess #Achievement"
        ],

        'growth': [
            "📈 Thrilled to announce another phase of significant growth for our company! "
            "We've expanded our reach, enhanced our offerings, and strengthened our position "
            "in the market. Grateful for the opportunity to serve our growing community of clients. #Growth #Expansion",

            "🌟 Celebrating remarkable growth momentum! Our strategic initiatives are "
            "yielding impressive results as we continue to scale and innovate. "
            "Excited about the opportunities that lie ahead! #CompanyGrowth #Innovation",

            "🎯 Achievement unlocked! Our growth trajectory continues to exceed expectations, "
            "reflecting our team's relentless pursuit of excellence. Thank you to our partners "
            "and customers for being part of this incredible journey. #GrowthMilestone #Partnership"
        ],

        'product_launch': [
            "🚀 Big news! We're excited to announce the launch of our latest innovation. "
            "After months of development and refinement, we're proud to bring this solution "
            "to market. Designed with our customers in mind, we believe it will transform "
            "how businesses approach their challenges. #ProductLaunch #Innovation #NewSolution",

            "✨ Today marks an exciting milestone in our product journey! We're thrilled "
            "to introduce our newest offering that addresses key industry challenges. "
            "This launch represents countless hours of collaboration, iteration, and customer insight. #NewProduct #Innovation #Launch",

            "💡 Innovation in action! We've officially launched our latest product designed "
            "to empower businesses like yours. This release embodies our commitment to "
            "solving real-world problems with cutting-edge technology. #ProductInnovation #TechLaunch #BusinessSolutions"
        ],

        'award_recognition': [
            "🏆 Honored to receive recognition for our efforts and achievements! "
            "This award validates our team's commitment to excellence and innovation. "
            "We're grateful for the opportunity to contribute meaningfully to our industry. #AwardWinner #Recognition #Excellence",

            "🌟 Thrilled to share that we've been recognized for our outstanding contributions! "
            "This honor reflects our team's dedication to delivering exceptional value. "
            "Thank you to everyone who has supported us on this journey. #IndustryRecognition #Excellence #TeamEffort",

            "👏 Grateful and humbled by this prestigious recognition! Our team's hard work "
            "and innovative approach have been acknowledged by industry peers. "
            "Motivated to continue pushing boundaries and delivering value. #Award #Recognition #Innovation"
        ],

        'team_expansion': [
            "👥 Exciting news! We're growing our team with talented professionals "
            "who share our vision and passion. Each new member brings unique expertise "
            "that strengthens our capabilities and culture. Welcome aboard! #TeamGrowth #Hiring #Culture",

            "🎉 Welcoming new talent to our family! Our team expansion reflects our "
            "confidence in future growth and our commitment to excellence. "
            "Thrilled to have such skilled professionals join our mission. #NewTeamMembers #Growth #TeamBuilding",

            "🤝 Expanding our circle of innovators! We've onboarded exceptional talent "
            "who will help drive our next phase of growth. Proud to attract professionals "
            "who share our values and vision. #TeamExpansion #Talent #Growth"
        ],

        'partnership': [
            "🤝 Strategic partnerships that drive value! We're excited to announce "
            "our collaboration with industry leaders to deliver enhanced solutions. "
            "Together, we're building stronger foundations for mutual success. #Partnership #Collaboration #StrategicAlliance",

            "🔗 Strengthening our ecosystem through meaningful partnerships! "
            "We're proud to join forces with organizations that share our commitment "
            "to innovation and excellence. Together, we achieve more. #StrategicPartnership #Collaboration #ValueCreation",

            "🤝 Partnership announcement! We're thrilled to collaborate with industry pioneers "
            "to expand our impact and deliver exceptional value. Excited about the opportunities "
            "this alliance presents. #Partnership #Alliance #Growth"
        ],

        'general': [
            "🌟 Reflecting on another successful period of growth and achievement! "
            "Our commitment to excellence continues to yield positive results. "
            "Thank you to our team, customers, and partners for your ongoing support. #Success #Gratitude #Growth",

            "🚀 Momentum builds upon momentum! We're proud of the progress made "
            "and excited about the opportunities ahead. Our focus remains on delivering "
            "exceptional value to our stakeholders. #Progress #Success #Future",

            "💡 Innovation drives impact! Our dedication to solving complex challenges "
            "continues to resonate with our customers. Committed to pushing boundaries "
            "and creating meaningful solutions. #Innovation #Impact #Solutions"
        ]
    }

    # Select appropriate templates based on achievement type
    if achievement_type in templates:
        selected_templates = templates[achievement_type]
    else:
        selected_templates = templates['general']

    # Randomly select a template
    template = random.choice(selected_templates)

    # Enhance the post with specific data if available
    enhanced_post = personalize_post(template, business_data)

    return enhanced_post


def personalize_post(template: str, business_data: Dict) -> str:
    """
    Personalize a LinkedIn post template with specific business data.

    Args:
        template: Template string to personalize
        business_data: Dictionary containing specific business information

    Returns:
        Personalized LinkedIn post content
    """

    # Replace placeholders with actual data if available
    personalized = template

    # Add company name if available
    company_name = business_data.get('company_name', 'our company')
    personalized = personalized.replace('our company', company_name)
    personalized = personalized.replace('our team', f'{company_name} team')

    # Add specific metrics if available
    if 'metric_value' in business_data and 'metric_type' in business_data:
        metric_value = business_data['metric_value']
        metric_type = business_data['metric_type']

        # Add specific metric information
        if metric_type.lower() in ['revenue', 'sales', 'income']:
            personalized += f"\n\n📊 Specifics: Achieved ${metric_value:,} in {metric_type.lower()}."
        elif metric_type.lower() in ['users', 'customers', 'clients']:
            personalized += f"\n\n👥 Growth: Reached {metric_value:,} {metric_type.lower()}."
        elif metric_type.lower() in ['growth', 'increase', 'percentage']:
            personalized += f"\n\n📈 Performance: Achieved {metric_value}% {metric_type.lower()}."
        else:
            personalized += f"\n\n📊 Achievement: Reached {metric_value} in {metric_type.lower()}."

    # Add time context if available
    if 'time_period' in business_data:
        time_period = business_data['time_period']
        personalized += f"\n\n📅 Period: {time_period}"

    # Add quote or testimonial if available
    if 'quote' in business_data:
        quote = business_data['quote']
        personalized += f"\n\n💬 Quote: \"{quote}\""

    # Add call to action if available
    if 'call_to_action' in business_data:
        cta = business_data['call_to_action']
        personalized += f"\n\n👉 {cta}"

    return personalized


def generate_business_achievement_data_example() -> Dict:
    """
    Generate example business achievement data for testing.

    Returns:
        Example business achievement data
    """

    examples = [
        {
            'type': 'revenue',
            'company_name': 'TechInnovate Inc.',
            'metric_value': 1000000,
            'metric_type': 'revenue',
            'time_period': 'Q4 2025',
            'quote': 'Excellence is never an accident. It is always the result of high intention.',
            'call_to_action': 'Connect with us to learn more about our solutions.'
        },
        {
            'type': 'growth',
            'company_name': 'GrowthTech Solutions',
            'metric_value': 250,
            'metric_type': 'customers',
            'time_period': 'past year',
            'quote': 'Growth is the only evidence of life.',
            'call_to_action': 'Join our growing community of satisfied customers.'
        },
        {
            'type': 'product_launch',
            'company_name': 'InnovateSoft',
            'metric_value': 'Advanced Analytics Platform',
            'metric_type': 'product',
            'time_period': 'January 2026',
            'quote': 'Innovation distinguishes between a leader and a follower.',
            'call_to_action': 'Discover how our new platform can transform your business.'
        },
        {
            'type': 'award_recognition',
            'company_name': 'Excellence Corp',
            'metric_value': 'Best Workplace Award',
            'metric_type': 'award',
            'time_period': '2026 Annual Awards',
            'quote': 'Recognition is the most powerful driver of engagement.',
            'call_to_action': 'Learn more about our award-winning approach.'
        }
    ]

    return random.choice(examples)


def format_linkedin_post(post_content: str, hashtags: Optional[List[str]] = None) -> str:
    """
    Format a LinkedIn post with proper structure and hashtags.

    Args:
        post_content: Raw post content to format
        hashtags: Optional list of hashtags to include

    Returns:
        Formatted LinkedIn post
    """

    # Default hashtags if none provided
    if not hashtags:
        hashtags = [
            'BusinessGrowth', 'Innovation', 'Leadership',
            'Entrepreneurship', 'Success', 'TeamWork'
        ]

    # Limit to 5-7 hashtags to avoid spammy appearance
    selected_hashtags = hashtags[:7]
    hashtag_line = ' '.join([f'#{tag}' for tag in selected_hashtags])

    # Combine content with hashtags
    formatted_post = f"{post_content}\n\n{hashtag_line}"

    # LinkedIn has a character limit, so we'll ensure it's reasonable
    if len(formatted_post) > 3000:  # Well below LinkedIn's ~3000 character limit
        # Truncate and add ...
        truncated = formatted_post[:2900] + "... (truncated)"
        return truncated

    return formatted_post


if __name__ == "__main__":
    # Example usage
    print("LinkedIn Post Generator - Example Usage")
    print("=" * 50)

    # Generate example achievement data
    example_data = generate_business_achievement_data_example()
    print(f"Example business data: {json.dumps(example_data, indent=2)}")

    # Generate a post based on the example data
    generated_post = generate_linkedin_post(example_data)
    print(f"\nGenerated LinkedIn post:\n{generated_post}")

    # Format with hashtags
    formatted_post = format_linkedin_post(generated_post)
    print(f"\nFormatted LinkedIn post:\n{formatted_post}")